import sys
import pandas as pd

def mkplot_concatenate(files, savename):
    ERR = -1
    f_data = dict()

    new_table = pd.DataFrame()

    for f in files:
        print(f)
        if "Reach" in f:
            f_data["Reach"] = pd.read_csv(f, sep=" ")
        elif "SeparateWPk" in f:
            f_data["WP"] = pd.read_csv(f, sep=" ")
        elif "SC" in f:
            f_data["SC"] = pd.read_csv(f, sep=" ")
        else:
            print("ERROR")

    props = ["Reach", "WP", "SC"]
    for prop in props:
        if prop not in f_data:
            continue
        p = f_data[prop]

        if prop == "SeparateWPk":
            prop = "WP"

        p.rename(columns={ c : "{} {}".format(c, prop).replace(" ","-") for c in p.columns if c != "instance"}, inplace=True)

        for c in p.columns:
            if c != "instance":
                new_table[c] = p[c]

    new_table.insert(loc=0, column='instance', value=["instance" + str(i) for i in range(len(new_table.index)) ])
    new_table.fillna(ERR,inplace=True)
    new_table.to_csv("{}.mkplot".format(savename),sep=" ", index=False)
    print(new_table)

if __name__ == '__main__':
    mkplot_concatenate([f for f in sys.argv[1:-1]], sys.argv[-1])