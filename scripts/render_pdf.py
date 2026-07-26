from pathlib import Path
import pypdfium2 as pdfium

source = Path('output/pdf/paper-mill-predictive-decision-support-architecture.pdf')
target = Path('output/png/paper-mill-predictive-decision-support-architecture-300dpi.png')
target.parent.mkdir(parents=True, exist_ok=True)
document = pdfium.PdfDocument(str(source))
page = document[0]
image = page.render(scale=300 / 72).to_pil()
image.save(target)
print(target, image.size)
