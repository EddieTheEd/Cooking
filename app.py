import os
import subprocess
import shutil
from io import BytesIO
from werkzeug.datastructures import FileStorage
from flask import Flask, render_template, request, send_file
from flask_compress import Compress
from glob import glob
from zipfile import ZipFile

app = Flask(__name__)
Compress(app)

class Options:
    def __init__(self, paper=None, shortedge=False, crop=True, outerMargin=40, innerMargin=150, topMargin=30, bottomMargin=30, signature=0, resolution=72):
        self.paper = paper
        self.shortedge = shortedge
        self.crop = crop
        self.outerMargin = outerMargin
        self.innerMargin = innerMargin
        self.topMargin = topMargin
        self.bottomMargin = bottomMargin
        self.signature = signature
        self.resolution = resolution

def booklify(file, opts):
    name = os.path.join(os.getcwd(), 'input.pdf')
    tmpFile = os.path.join(os.getcwd(), 'crop-tmp.pdf')

    file.save(name)

    if not os.path.isfile(name):
        raise FileNotFoundError("File not found.")

    bboxName = b"%%HiResBoundingBox:"

    if opts.crop:
        p = subprocess.Popen(
            ["pdfcrop", "--verbose", "--resolution", str(opts.resolution), name, tmpFile],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = p.communicate()
        if err:
            raise RuntimeError(f"Problem getting bounds: {err.decode()}")

        lines = out.splitlines()
        bboxes = [s[len(bboxName) + 1 :] for s in lines if s.startswith(bboxName)]
        bounds = [[float(x) for x in bbox.split()] for bbox in bboxes]
        minLOdd = min([bound[0] for bound in bounds[::2]])
        maxROdd = max([bound[2] for bound in bounds[::2]])
        if len(bboxes) > 1:
            minLEven = min([bound[0] for bound in bounds[1::2]])
            maxREven = max([bound[2] for bound in bounds[1::2]])
        else:
            minLEven = minLOdd
            maxREven = maxROdd
        minT = min([bound[1] for bound in bounds])
        maxB = max([bound[3] for bound in bounds])

        widthOdd = maxROdd - minLOdd
        widthEven = maxREven - minLEven
        maxWidth = max(widthOdd, widthEven)
        minLOdd -= maxWidth - widthOdd
        maxREven += maxWidth - widthEven

        p = subprocess.Popen(
            [
                "pdfcrop",
                "--bbox-odd",
                "{L} {T} {R} {B}".format(
                    L=minLOdd - opts.innerMargin / 2,
                    T=minT - opts.topMargin,
                    R=maxROdd + opts.outerMargin,
                    B=maxB + opts.outerMargin,
                ),
                "--bbox-even",
                "{L} {T} {R} {B}".format(
                    L=minLEven - opts.outerMargin,
                    T=minT - opts.topMargin,
                    R=maxREven + opts.innerMargin / 2,
                    B=maxB + opts.outerMargin,
                ),
                "--resolution",
                str(opts.resolution),
                name,
                tmpFile,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = p.communicate()
        if err:
            raise RuntimeError(f"Problem with cropping: {err.decode()}")
    else:
        shutil.copy(name, tmpFile)

    pdfJamCallList = [
        "pdfjam",
        "--landscape",
        "--suffix",
        "book",
        tmpFile,
    ]

    if opts.signature != 0:
        pdfJamCallList.append("--signature")
        pdfJamCallList.append(str(opts.signature))
    else:
        pdfJamCallList.append("--booklet")
        pdfJamCallList.append("true")

    if opts.paper is not None:
        pdfJamCallList.append("--paper")
        pdfJamCallList.append(opts.paper)

    if opts.shortedge:
        p = subprocess.Popen(
            ["kpsewhich", "everyshi.sty"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = p.communicate()
        if not out:
            raise RuntimeError("The everyshi.sty latex package is needed for short-edge.")
        else:
            pdfJamCallList.append("--preamble")
            pdfJamCallList.append(
                r"\usepackage{everyshi}\makeatletter\EveryShipout{\ifodd\c@page\pdfpageattr{/Rotate 180}\fi}\makeatother"
            )

    p = subprocess.Popen(pdfJamCallList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()

    output_file_name = os.path.join(os.getcwd(), tmpFile[:-4] + "-book.pdf")
    final_output_name = os.path.join(os.getcwd(), name[:-4] + "-book.pdf")
    os.rename(output_file_name, final_output_name)

    with open(name[:-4] + "-book.pdf", "rb") as f:
        result_pdf = BytesIO(f.read())

    os.remove(os.path.join(os.getcwd(), name))
    os.remove(os.path.join(os.getcwd(), tmpFile))
    os.remove(final_output_name)

    return result_pdf

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No files uploaded', 400
        
        files = request.files.getlist('file')
        if len(files) == 0:
            return 'No files selected', 400

        if len(files) == 1:
            original_filename = files[0].filename
            base, ext = os.path.splitext(original_filename)
            output_filename = f"{base}-book{ext}"

            opts = Options()
            output_pdf = booklify(files[0], opts)
            return send_file(output_pdf, mimetype='application/pdf', as_attachment=True, download_name=output_filename)

        else:
            stream = BytesIO()
            with ZipFile(stream, 'w') as zf:
                for file in files:
                    if file and file.filename != '':
                        original_filename = file.filename
                        base, ext = os.path.splitext(original_filename)
                        output_filename = f"{base}-book{ext}"

                        opts = Options()
                        output_pdf = booklify(file, opts)

                        zf.writestr(output_filename, output_pdf.getvalue())
                    else:
                        return 'One or more files are empty', 400

            stream.seek(0)
            return send_file(stream, mimetype='application/zip', as_attachment=True, download_name='Cooking_tray.zip')

    return render_template('index.html')

@app.route('/details')
def details():
    return render_template('details.html')

@app.route('/explainer')
def explainer():
    return render_template('explainer.html')

@app.route('/local')
def local():
    return render_template('local.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5100)
