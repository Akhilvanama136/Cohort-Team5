import base64
import logging
import os
import requests
from io import BytesIO
from typing import List, Optional, Tuple

from PIL import Image
from src.vector_db import MedicalRetriever
from src.image_safety import (
    VISION_SAFETY_RULES,
    build_safety_preamble,
    detect_possible_annotations,
    validate_imaging_safety,
)

logger = logging.getLogger("MedicalPathologyAPI")

MAX_IMAGE_SIDE = 384
IMAGE_JPEG_QUALITY = 75
MAX_CHUNK_CHARS = 200
RAG_TOP_K_IMAGE = 1
OLLAMA_KEEP_ALIVE = "30m"
IMAGE_CALL_TIMEOUT = 90
TEXT_CALL_TIMEOUT = 150


def _optimize_image_b64(image_b64: str, max_size: int = MAX_IMAGE_SIDE) -> str:
    raw = base64.b64decode(image_b64)
    img = Image.open(BytesIO(raw))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    elif img.mode == "L":
        img = img.convert("RGB")
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=IMAGE_JPEG_QUALITY, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _ollama_base(ollama_url: str) -> str:
    return ollama_url.rsplit("/", 2)[0]


def _ollama_ready(ollama_url: str, model_name: str, timeout: float = 5.0) -> bool:
    try:
        r = requests.get(f"{_ollama_base(ollama_url)}/api/tags", timeout=timeout)
        if r.status_code != 200:
            return False
        names = {m.get("name", "").split(":")[0] for m in r.json().get("models", [])}
        return model_name.split(":")[0] in names
    except requests.exceptions.RequestException:
        return False


class MedGemmaQA:
    """Retrieval + MedGemma via Ollama for text Q&A and image care reports."""

    def __init__(self, ollama_url: str = None, model_name: str = "medgemma"):
        self.ollama_url = ollama_url or os.getenv(
            "OLLAMA_URL", "http://localhost:11434/api/generate"
        )
        self.model_name = model_name
        self.retriever = MedicalRetriever()

    def warmup_model(self) -> bool:
        if not _ollama_ready(self.ollama_url, self.model_name):
            logger.warning("Ollama not ready — skipping model warmup")
            return False
        try:
            r = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": "Ready.",
                    "stream": False,
                    "keep_alive": OLLAMA_KEEP_ALIVE,
                    "options": {"num_predict": 1},
                },
                timeout=180,
            )
            ok = r.status_code == 200
            if ok:
                logger.info("MedGemma model warmed up in Ollama")
            return ok
        except requests.exceptions.RequestException as exc:
            logger.warning("Model warmup failed: %s", exc)
            return False

    def _call_ollama(
        self,
        prompt: str,
        *,
        images: Optional[List[str]] = None,
        num_predict: int = 256,
        timeout: int = 90,
    ) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "keep_alive": OLLAMA_KEEP_ALIVE,
            "options": {"temperature": 0.1, "num_predict": num_predict},
        }
        if images:
            payload["images"] = images

        r = requests.post(self.ollama_url, json=payload, timeout=timeout)
        if r.status_code == 200:
            return r.json().get("response", "").strip()
        return f"Error: Ollama API returned status {r.status_code}. {r.text[:200]}"

    def _try_ollama(
        self,
        prompt: str,
        *,
        images: Optional[List[str]] = None,
        num_predict: int = 256,
        timeout: int = 90,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Returns (response_text, error_kind). error_kind is 'timeout' or error message."""
        try:
            text = self._call_ollama(
                prompt, images=images, num_predict=num_predict, timeout=timeout
            )
            if text.startswith("Error:"):
                return None, text
            return text, None
        except requests.exceptions.Timeout:
            return None, "timeout"
        except requests.exceptions.RequestException as exc:
            return None, str(exc)

    def format_context(self, retrieved_chunks, max_chars: int = MAX_CHUNK_CHARS) -> str:
        formatted = []
        for i, chunk in enumerate(retrieved_chunks):
            text = chunk["text"]
            if len(text) > max_chars:
                text = text[:max_chars] + "…"
            page_info = f" (Page {chunk['page']})" if chunk.get("page") != "N/A" else ""
            formatted.append(
                f"[{i + 1}] {chunk['source']}{page_info}: {text}"
            )
        return "\n".join(formatted)

    def _chunks_to_sources(self, chunks) -> List[dict]:
        return [
            {
                "source": c["source"],
                "page": c["page"],
                "category": c["category"],
                "score": c["score"],
            }
            for c in chunks
        ]

    def _empty_image_meta(self) -> dict:
        return {
            "vision_summary": None,
            "safety_flags": [],
            "requires_radiologist_review": True,
            "imaging_confidence": "low",
        }

    def _marker_note(self, annotation_hint: dict) -> str:
        if annotation_hint.get("annotations_likely"):
            return (
                "NOTE: Possible arrows/markers on image — describe what they point to FIRST.\n"
            )
        return ""

    def answer_question(self, question: str, top_k: int = 10, category: str = None) -> dict:
        try:
            chunks = self.retriever.search(question, top_k=top_k, category=category)
        except Exception as e:
            logger.warning("Retrieval failed: %s", e)
            chunks = []

        context_str = self.format_context(chunks) if chunks else "No relevant context found."
        system_prompt = (
            "You are an AI Medical Pathology Assistant. Answer based ONLY on the Context below.\n"
            "If the answer cannot be found in the Context, reply exactly: "
            "\"I couldn't find sufficient medical evidence.\"\n"
            "Always mention the medical source name from the Context."
        )
        final_prompt = (
            f"Instructions:\n{system_prompt}\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question:\n{question}\n\nAnswer:"
        )

        try:
            response_text = self._call_ollama(final_prompt, num_predict=512, timeout=TEXT_CALL_TIMEOUT)
        except requests.exceptions.RequestException as e:
            response_text = (
                f"Error communicating with local MedGemma (Ollama): {e}\n"
                f"Ensure Ollama is running and '{self.model_name}' is pulled."
            )

        return {
            "answer": response_text,
            "context_used": context_str,
            "sources": self._chunks_to_sources(chunks),
        }

    def _single_pass_image_report(
        self, question: str, image_b64: str, context_str: str, annotation_hint: dict
    ) -> Tuple[Optional[str], Optional[str]]:
        """One multimodal call — faster than two sequential calls on CPU."""
        prompt = (
            f"{VISION_SAFETY_RULES}\n"
            f"{self._marker_note(annotation_hint)}\n"
            "Analyze this medical image and write an EDUCATIONAL patient care report.\n"
            "Check for arrows/markers first. Never say 'clear' or 'normal' unless highly certain.\n"
            "Ground diet/meds/treatment in Context only.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Request:\n{question}\n\n"
            "Use these markdown headers:\n"
            "## Imaging Findings\n## Likely Condition\n## Disease Overview\n"
            "## Patient Precautions\n## Diet & Nutrition\n"
            "## Medications & Treatment\n## Clinical Follow-up\n\nReport:"
        )
        return self._try_ollama(
            prompt,
            images=[image_b64],
            num_predict=420,
            timeout=IMAGE_CALL_TIMEOUT,
        )

    def _fast_vision_only(self, image_b64: str, annotation_hint: dict) -> Tuple[Optional[str], Optional[str]]:
        """Shorter vision pass used when single-pass times out."""
        prompt = (
            f"{VISION_SAFETY_RULES}\n{self._marker_note(annotation_hint)}"
            "Brief radiology read. Format:\n"
            "ANNOTATIONS_PRESENT: yes/no\nANNOTATION_TARGETS:\nMODALITY:\nREGION:\n"
            "FINDINGS:\nABNORMALITY_PRESENT: yes/no/uncertain\nCONFIDENCE: low/medium/high\n"
            "LIKELY_CONDITION:\nSAFETY_NOTE:"
        )
        return self._try_ollama(
            prompt, images=[image_b64], num_predict=150, timeout=120
        )

    def _rag_fallback_report(
        self, question: str, context_str: str, annotation_hint: dict, vision_summary: Optional[str]
    ) -> str:
        """Text-only fallback — always returns useful RAG-grounded guidance."""
        marker_block = ""
        if annotation_hint.get("annotations_likely"):
            marker_block = (
                "IMPORTANT: Image may contain arrows/markers (teaching case). "
                "Radiologist must inspect the marked region manually.\n"
            )

        imaging_block = (
            f"Prior AI vision (partial):\n{vision_summary}\n"
            if vision_summary
            else "Automated image read did not complete (timeout). Do NOT assume lungs are clear.\n"
        )

        prompt = (
            "Write an EDUCATIONAL patient care report using ONLY the Context below.\n"
            f"{marker_block}"
            "For Imaging Findings: state that AI image read failed or was partial — radiologist review required.\n"
            "Do NOT claim lungs are clear or normal.\n\n"
            f"{imaging_block}\n"
            f"Context:\n{context_str}\n\n"
            f"Request:\n{question}\n\n"
            "Headers: ## Imaging Findings ## Likely Condition ## Disease Overview "
            "## Patient Precautions ## Diet & Nutrition ## Medications & Treatment ## Clinical Follow-up\n\nReport:"
        )
        text, err = self._try_ollama(prompt, num_predict=400, timeout=TEXT_CALL_TIMEOUT)
        if text:
            return text

        # Last resort — structured template without LLM
        return self._static_fallback_report(context_str, annotation_hint, vision_summary)

    def _static_fallback_report(
        self, context_str: str, annotation_hint: dict, vision_summary: Optional[str]
    ) -> str:
        """Guaranteed response when all Ollama calls fail."""
        marker = ""
        if annotation_hint.get("annotations_likely"):
            marker = (
                "\n**Marker alert:** Possible arrows on image — manually review the "
                "pointed region (e.g. hilar/perihilar on chest X-rays).\n"
            )
        vision = vision_summary or "*AI vision did not complete — radiologist review mandatory.*"
        return (
            "## Imaging Findings\n"
            f"Automated AI image analysis could not be completed on this hardware.{marker}\n"
            f"Partial vision output:\n{vision}\n\n"
            "## Likely Condition\n"
            "Cannot be determined by AI — clinical and radiological correlation required.\n\n"
            "## Disease Overview\n"
            "See retrieved knowledge-base excerpts below and consult a specialist.\n\n"
            "## Patient Precautions\n"
            "Do not rely on this AI output. Seek immediate care for worsening symptoms.\n\n"
            "## Diet & Nutrition\n"
            "Maintain a balanced diet rich in protein, fruits, and vegetables to support general health and recovery. Specific clinical dietary recommendations depend on the final medical diagnosis.\n\n"
            "## Medications & Treatment\n"
            "Medication regimens and treatment plans must be customized by an oncologist or general physician. Do not start or modify any clinical treatments without a prescription.\n\n"
            "## Clinical Follow-up\n"
            "Formal radiologist read required before any clinical decision.\n\n"
            "---\n**Retrieved medical context:**\n"
            f"{context_str[:2000]}"
        )

    def analyze_image(self, question: str, image_b64: str, category: str = None, report_content: str = None) -> dict:
        """
        Resilient image pipeline:
          1) Single multimodal pass (image + compact RAG + report) — one Ollama load
          2) On timeout: fast vision + RAG text fallback
          3) On total failure: static template with RAG excerpts (never empty)
        """
        meta = self._empty_image_meta()

        if not _ollama_ready(self.ollama_url, self.model_name):
            return {
                "answer": (
                    "Image analysis unavailable: Ollama is not running or "
                    f"'{self.model_name}' is not installed.\n"
                    "Start Ollama: `ollama serve` then `ollama pull medgemma`"
                ),
                "sources": [],
                **meta,
            }

        try:
            raw_b64 = image_b64
            image_b64 = _optimize_image_b64(image_b64)
            annotation_hint = detect_possible_annotations(raw_b64)
        except Exception as e:
            return {"answer": f"Could not process uploaded image: {e}", "sources": [], **meta}

        rag_query = (
            f"{question} precautions diet medications treatment "
            f"clinical follow-up patient care"
        )
        try:
            chunks = self.retriever.search(rag_query, top_k=RAG_TOP_K_IMAGE, category=category)
        except Exception as e:
            logger.warning("Retrieval failed during image analysis: %s", e)
            chunks = []

        sources = self._chunks_to_sources(chunks)
        context_str = (
            self.format_context(chunks) if chunks else "No matching documents in knowledge base."
        )

        # Add report content to context if provided
        if report_content:
            context_str += f"\n\n---\n**Uploaded Medical Report:**\n{report_content[:3000]}"
            logger.info(f"Report content added to context: {len(report_content)} characters")

        vision_summary = None
        care_report = None
        fallback_used = False

        # --- Primary: single multimodal call ---
        logger.info("Image analysis: single-pass multimodal")
        care_report, err = self._single_pass_image_report(
            question, image_b64, context_str, annotation_hint
        )
        if err or not care_report:
            logger.warning("Single-pass failed/timed out (%s) — RAG fallback", err)
            fallback_used = True
            care_report = self._rag_fallback_report(
                question, context_str, annotation_hint, None
            )

        if fallback_used:
            meta["safety_flags"].append(
                "Primary image analysis timed out — partial/fallback report generated. "
                "Radiologist must review the scan."
            )

        if not vision_summary and care_report and not fallback_used:
            # Successful single-pass — no separate vision blob needed
            vision_summary = "(combined single-pass report)"

        meta["vision_summary"] = vision_summary
        safety = validate_imaging_safety(
            vision_summary if vision_summary and "combined" not in vision_summary else "",
            care_report or "",
            annotation_hint,
        )
        meta["safety_flags"].extend(safety["flags"])
        meta["requires_radiologist_review"] = True
        meta["imaging_confidence"] = safety.get("imaging_confidence", "low")

        if fallback_used or meta["safety_flags"]:
            preamble = build_safety_preamble(
                meta["safety_flags"],
                vision_summary if vision_summary and "combined" not in vision_summary else (
                    "Single-pass report — verify all findings against the image."
                ),
            )
            final_answer = preamble + (care_report or "")
        else:
            final_answer = (
                "> **Radiologist review required** — AI output is educational only.\n\n"
                + (care_report or "")
            )

        return {
            "answer": final_answer,
            "sources": sources,
            **meta,
        }


if __name__ == "__main__":
    qa = MedGemmaQA()
    print("MedGemma QA client initialized.")
