import os
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
import StringIO

path_read = "raw_data/pdf/"
path_save = "raw_data/json/"
month = ""


def convert_files():
    open_files()


def open_files():
    files = []
    file_contents = ""

    if not os.path.exists(path_read):
        raise Exception("Read Path Does Not Exist.")
    else:
        subdirs = os.listdir(path_read)

    for directory in subdirs:
        files = os.listdir(path_read + directory)

        if len(files) > 0:
            for file_name in files:
                if file_name.find(".pdf") > 0:
                    os.chdir(path_read + directory)
                    with open(file_name, "rb") as pdf_file:
                        print(file_name)
                        raw_contents = convert_file(pdf_file, file_name)
                        file_contents = parse_file(raw_contents)
                    write_file(file_contents, file_name, directory)
                    os.chdir('../../../')


def write_file(file_data, file_name, directory):
    os.chdir('../../../')
    path = path_save + directory
    if not os.path.exists(path):
        parts = path.split("/")
        for part in parts:
            if len(part) > 0:
                if not os.path.exists(part):
                    os.mkdir(part)
                    os.chdir(part)
                else:
                    os.chdir(part)
    else:
        os.chdir(path)

    file_name = month + "_" + file_name.replace(".pdf", ".json")
    with open(file_name, "wb") as f:
        f.write(file_data)

    print(file_data)


def parse_file(raw_contents):
    # print(raw_contents)
    lines = raw_contents.split('\n')
    x = 0
    precinct_found = False
    description_found = False
    mtd_found = False
    ytd_found = False
    precinct_line = -1
    month_line = -1
    description_line = -1
    mtd_line = -1
    ytd_line = -1

    for line in lines:
        if line.find('Moving Violations') != -1 and not precinct_found:
            precinct_line = x + 2
            if lines[precinct_line + 1] == '':
                month_line = precinct_line + 2
            else:
                month_line = precinct_line + 1
        elif line.find('Description') != -1 and not description_found:
            description_line = x + 2
        elif line.find('MTD') != -1 and not mtd_found:
            mtd_line = x + 1
        elif line.find('YTD') != -1 and not ytd_found:
            ytd_line = x + 1
        x += 1

    return build_JSON(lines, precinct_line, month_line, description_line, mtd_line, ytd_line)


def build_JSON(lines, precinct_line, month_line, description_line, mtd_line, ytd_line):
    global month
    x = 0
    started_violations = False
    JSON = "{"
    for line in lines:
        if x == precinct_line:
            JSON += "\"precinct\":\"" + line + "\","
            month = str(lines[month_line])[:-1]
            JSON += "\"month\":\"" + month + "\","
        elif x >= description_line:
            if line == "":
                break

            if not started_violations:
                JSON += "\"violations\":["
                started_violations = True

            JSON += "{\"name\":\"" + line + "\","
            JSON += "\"mtd\":" + lines[(x - description_line) + mtd_line] + ","
            JSON += "\"ytd\":" + lines[(x - description_line) + ytd_line] + "},"
        x += 1

    JSON = JSON[:-1]
    JSON += "]}"
    # print JSON
    return JSON


def convert_file(pdf_file, file_name):
    parser = PDFParser(pdf_file)
    pdf = PDFDocument(parser)
    pdf.initialize("")
    if not pdf.is_extractable:
        raise PDFPage.PDFTextExtractionNotAllowed("Document does not allow text extraction: " + file_name)

    resource = PDFResourceManager()
    laparams = LAParams()
    output = StringIO.StringIO()
    device = TextConverter(resource, output, codec='utf-8', laparams=laparams)

    interpreter = PDFPageInterpreter(resource, device)
    for page in PDFPage.create_pages(pdf):
        interpreter.process_page(page)

    return output.getvalue()


convert_files()