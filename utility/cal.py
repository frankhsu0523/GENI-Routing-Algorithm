import os, sys
import csv
import pickle
import re

class Calculate:

    def __init__(self, file = None, path_file = None):
        if file:
            self.demand_map_file = self.get_demand_map_file( file )
        else:
            self.demand_map_file = None
        if path_file:
            self.file_dir = os.path.dirname(os.path.realpath(path_file))
            self.path = self.get_path( path_file )
        else:
            self.file_dir = None
            self.path = None
        self.data = list()
        #for i in self.path:
            #print(i)

    def set_demand_map_file(self, file ):
        self.demand_map_file = file

    def set_path(self, path_file):
        self.file_dir = os.path.dirname(os.path.realpath(path_file))
        self.path = self.get_path( path_file )

    def get_data(self, dirname = 'data'):
        #for i in os.listdir( dirname ):
            #print('data',i)

        #for p in self.path:
        for i, d in self.demand_map_file.items():
            src, dst, port, path,size = i
            #fName = self.demand_map_file[p]
            fName = d
            if os.path.exists(dirname+'/' + fName):
                with open(dirname+'/'+fName, 'r') as f:
                    data = f.read()
                    result = re.findall(r'\d*\.?\d*\sKbits', data)
                    print(data)
                    if len(result) != 0:
                        value = result[0].split()[0]
                        if float(size) - float(value) < -1.0 :
                            print(size)
                            print(data)
                        if value == 0:
                            print(result)
                    else:
                        value = 0
                    self.data.append([src,dst,size,float(value)])

    def write_data(self, fName):
        with open(fName, 'w') as f:
            print(fName)
            writer = csv.writer(f)
            writer.writerows(self.data)
    def get_demand_map_file(self, file):
        with open(file, 'rb') as file:
            return pickle.load(file)

    def get_path(self, file):
        with open(file, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            path_list = list()
            for row in reader:
                src, dst, path, size = row[0], row[1], tuple(row[3:-1]), float(row[-1])
                path_list.append((src,dst,path,size))
        return path_list





def main():
    if len(sys.argv) < 2:
        print('no argument')
        sys.exit()
    if sys.argv[1].startswith('--'):
        option = sys.argv[1][2:]
        if option == 'help':
            print("python3 'cal.py' 'demand_map_file' 'instance_path/xxx.csv'")
    else:
        file = sys.argv[1]
        path_file = sys.argv[2]

        cal = Calculate( file, path_file )
        cal.get_data()
        cal.write_data(path_file.split('/')[2])


if __name__ == '__main__':
    main()
