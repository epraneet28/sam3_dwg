#!/usr/bin/env python3
"""Download SAM3 model weights from Hugging Face."""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def download_sam3_model(output_path: str = "models/sam3.pt", force: bool = False) -> Path:
    """
    Download SAM3 model weights from Hugging Face.

    Args:
        output_path: Path to save the model
        force: Whether to re-download if file exists

    Returns:
        Path to the downloaded model
    """
    output_path = Path(output_path)

    if output_path.exists() and not force:
        logger.info(f"Model already exists at {output_path}")
        return output_path

    logger.info("Downloading SAM3 model from Hugging Face (facebook/sam3)...")
    logger.info("Note: You must have requested and received access to SAM3 on Hugging Face")
    logger.info("Visit: https://huggingface.co/facebook/sam3")

    try:
        from huggingface_hub import hf_hub_download

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Download from Hugging Face
        logger.info("Downloading... (this may take several minutes, ~3.3GB)")

        downloaded_path = hf_hub_download(
            repo_id="facebook/sam3",
            filename="sam3.pt",
            local_dir=str(output_path.parent),
        )

        logger.info(f"Model downloaded successfully to {downloaded_path}")
        return Path(downloaded_path)

    except ImportError:
        logger.error(
            "huggingface_hub not installed. Install with: pip install huggingface_hub"
        )
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg or "not found" in error_msg.lower():
            logger.error(
                "\n" + "="*70 + "\n"
                "AUTHENTICATION ERROR: You need access to the SAM3 model.\n\n"
                "Steps to fix:\n"
                "1. Visit https://huggingface.co/facebook/sam3\n"
                "2. Click 'Request Access to Repository'\n"
                "3. Wait for Meta to approve your request\n"
                "4. Login with: huggingface-cli login\n"
                "   (or: python -c 'from huggingface_hub import login; login()')\n"
                "5. Re-run this script\n"
                + "="*70
            )
        else:
            logger.error(f"Failed to download model: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Download SAM3 model weights from Hugging Face",
        epilog="Note: Requires Hugging Face access approval for facebook/sam3"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="models/sam3.pt",
        help="Output path for model weights (default: models/sam3.pt)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force re-download even if file exists",
    )

    args = parser.parse_args()

    output_path = download_sam3_model(args.output, args.force)
    print(f"\n✅ Model ready at: {output_path}")
    print(f"   License: Meta SAM3 License (permissive, commercial use allowed)")
    print(f"   Size: ~3.3GB")


if __name__ == "__main__":
    main()
