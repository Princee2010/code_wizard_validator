import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
import os


def generate_qr_code(certificate_id: str, base_url: str, output_dir: str) -> str:
    """Generate a styled QR code and return its filename."""
    verification_url = f"{base_url}/verify/{certificate_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)

    try:
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=SolidFillColorMask(
                back_color=(255, 255, 255),
                front_color=(15, 23, 64)
            )
        )
    except Exception:
        img = qr.make_image(fill_color="#0F1740", back_color="white")

    filename = f"qr_{certificate_id}.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    return filename
