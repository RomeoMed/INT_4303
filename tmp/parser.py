import csv

def main():
    in_file = './courses.csv'
    out_file = './updated_courses.csv'

    term_dict = {
        "10": "Fall",
        "20": "Spring",
        "30": "Summer"
    }

    eng = ["BME","DIS","EAE","ECE","ECO","EEE","EEM","EGE","EIE","EME","EMS","ESE","GCC",
           "GCE","GCF","GCL","GCM","GCT","MRE","TAS","TCE","TCO","TEE","TIE","TME"]
    arch = ["ARC", "IDD", "URB", "ARI", "ART", "ATD", "DES", "GAM"]
    busit = ["ACC", "DIS", "ECN", "FIN", "HRM", "INT", "MBA", "MGT", "MIS", "MKT", "MSL", "RES"]
    arts = ["BIO", "CHM", "COM", "CRW", "ESL", "FSC", "GCM", "GLG", "LDR", "LLT", "MCO", "MCS",
            "NUR", "PHY", "PSC", "PSY", "SAP", "SCE", "SSC"]

    out_headers = ["year", "term", "college_id", "crn", "course_name", "dept", "campus", "course_num", "num"]

    output = open(out_file, 'w')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(out_headers)

    with open(in_file, newline='') as in_f:
        has_header = csv.Sniffer().has_header(in_f.read(1024))
        in_f.seek(0)  # Rewind.
        reader = csv.DictReader(in_f)
        if has_header:
            next(reader)
        for row in reader:
            term = row['term']
            crn = row['crn']
            dept = row['dept']
            name = row['course_name']
            campus = row['campus']
            c_num  = row['course_num']
            num = row['num']

            year = term[:4]
            term_code = term[4:]
            term_str = term_dict[str(term_code)]

            college_id = 0
            if dept in eng:
                college_id = 1
            elif dept in arch:
                college_id = 2
            elif dept in busit:
                college_id = 3
            elif dept in arts:
                college_id = 4
            else:
                college_id = "n/a"

            writer.writerow([year, term_str, college_id, crn, name, dept, campus, c_num, num])
    output.close()

if __name__ == '__main__':
    main()