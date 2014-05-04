import os
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
import StringIO
import json

path_read = "raw_data/pdf/"
path_save = "raw_data/json/precincts/"
month = ""
dir_year = 2013
dir_mo = 0

precincts = ["001", "030", "062", "088", "115", "005", "032", "063", "090", "120", "006", "033", "066", "094", "121", "007", "034", "067", "100", "122", "009", "040", "068", "101", "123", "010", "041", "069", "102", "city", "013", "042", "070", "103", "cot", "014", "043", "071", "104", "housing", "017", "044", "072", "105", "patrol", "018", "045", "073", "106", "pbbn", "019", "046", "075", "107", "pbbs", "020", "047", "076", "108", "pbbx", "022", "048", "077", "109", "pbmn", "023", "049", "078", "110", "pbms", "024", "050", "079", "111", "pbqn", "025", "052", "081", "112", "pbqs", "026", "060", "083", "113", "pbsi", "028", "061", "084", "114", "transit"]
precinct_data = []

def convert_files():
    open_files()


def get_directory_contents(path):
    files = os.listdir(path)

    for file in files:
        yield file


def get_directories(path):
    global dir_year, dir_mo

    if not os.path.exists(path):
        raise Exception("Read Path Does Not Exist.")
    else:
        subdirs = os.listdir(path)

    for directory in subdirs:
        parts = directory.split("_")
        dir_year = int(parts[0])
        dir_mo = int(parts[1])
        yield directory


# TODO: Use csv or A for all.
def get_precincts():
    for precinct in precincts:
         yield precinct


def open_files():
    files = []
    for precinct in get_precincts():
        precinct_data = {}
        monthly_precinct_totals = []
        precinct_data["precinct"] = precinct
        for directory in get_directories(path_read):
            for file_name in get_directory_contents(path_read + directory):
                if file_name.find(".pdf") >= 0 and file_name.find(precinct) >= 0:
                    os.chdir(path_read + directory)
                    with open(file_name, "rb") as pdf_file:
                        print(file_name)
                        raw_contents = convert_file(pdf_file, file_name)
                        index_locations = parse_file(raw_contents)
                        month_data = build_monthly_data(index_locations)
                        precinct_data["precinct_name"] = month_data.pop("precinct", "")
                        monthly_precinct_totals.append(month_data)
                    os.chdir("../../../")
        write_file(monthly_precinct_totals, precinct_data, directory)
        os.chdir("../../../")
        print(os.getcwd())


def build_directory(path):
    parts = path.split("/")
    for part in parts:
        if len(part) > 0:
            print(os.getcwd())
            if not os.path.exists(part):
                os.mkdir(part)
                os.chdir(part)
            else:
                os.chdir(part)


def open_directory(directory):
    # os.chdir("../../../")
    # path = path_save + directory
    if not os.path.exists(path_save):
        build_directory(path_save)
    else:
        os.chdir(path_save)


def write_file(totals, precinct_data, directory):
    file_name = precinct_data["precinct"] + "_precinct.json"

    file_data = {
        "precinct": precinct_data["precinct_name"],
        "precinct_id": precinct_data["precinct"],
        "monthly_totals": totals
    }

    open_directory(directory)
    print("writing: " + path_save + file_name)
    with open(file_name, "wb") as f:
        f.write(json.dumps(file_data))


def parse_file(raw_contents):
    # print(raw_contents)
    lines = raw_contents.split("\n")
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
        if line.find("Moving Violations") != -1 and not precinct_found:
            precinct_line = x + 2
            if lines[precinct_line + 1] == "":
                month_line = precinct_line + 2
            else:
                month_line = precinct_line + 1
        elif line.find("Description") != -1 and not description_found:
            description_line = x + 2
        elif line.find("MTD") != -1 and not mtd_found:
            mtd_line = x + 1
        elif line.find("YTD") != -1 and not ytd_found:
            ytd_line = x + 1
        x += 1

    return {
        "lines": lines,
        "precinct_line": precinct_line,
        "month_line": month_line,
        "description_line": description_line,
        "mtd_line": mtd_line,
        "ytd_line": ytd_line
    }


def build_monthly_data(index_locations):
    global month
    
    lines = index_locations["lines"]
    precinct_line = index_locations["precinct_line"]
    month_line = index_locations["month_line"]
    description_line = index_locations["description_line"]
    mtd_line = index_locations["mtd_line"]
    ytd_line = index_locations["ytd_line"]

    x = 0
    started_violations = False

    data = {}

    for line in lines:
        if x == precinct_line:
            month = str(lines[month_line])[:-1]
            data["precinct"] = line
            data["month"] = month
            data["year"] = dir_year
            data["month_no"] = dir_mo
        elif x >= description_line:
            if line == "":
                break

            if not started_violations:
                data["violations"] = []
                started_violations = True

            try:
                mtd = int(lines[(x - description_line) + mtd_line])
                ytd = int(lines[(x - description_line) + ytd_line])
            except:
                mtd = lines[(x - description_line) + mtd_line]
                ytd = lines[(x - description_line) + ytd_line]

            data["violations"].append({
                    "name": line,
                    "mtd": mtd,
                    "ytd": ytd
                })
        x += 1

    # print(data)
    return data


def convert_file(pdf_file, file_name):
    parser = PDFParser(pdf_file)
    pdf = PDFDocument(parser)
    pdf.initialize("")
    if not pdf.is_extractable:
        raise PDFPage.PDFTextExtractionNotAllowed("Document does not allow text extraction: " + file_name)

    resource = PDFResourceManager()
    laparams = LAParams()
    output = StringIO.StringIO()
    device = TextConverter(resource, output, codec="utf-8", laparams=laparams)

    interpreter = PDFPageInterpreter(resource, device)
    for page in PDFPage.create_pages(pdf):
        interpreter.process_page(page)

    return output.getvalue()


convert_files()
