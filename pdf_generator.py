from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def generate_report(
    filename,
    disease,
    confidence,
    fertilizer,
    treatment
):

    pdf = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "AI Crop Disease Detection Report",
            styles['Title']
        )
    )

    content.append(Spacer(1, 20))

    content.append(
        Paragraph(
            f"<b>Disease:</b> {disease}",
            styles['BodyText']
        )
    )

    content.append(
        Paragraph(
            f"<b>Confidence:</b> {confidence}%",
            styles['BodyText']
        )
    )

    content.append(
        Paragraph(
            f"<b>Recommended Fertilizer:</b> {fertilizer}",
            styles['BodyText']
        )
    )

    content.append(
        Paragraph(
            f"<b>Treatment:</b> {treatment}",
            styles['BodyText']
        )
    )

    pdf.build(content)