
HOST="127.0.0.1"
PORT=6379

import urlparse, ast
import os, redis, json
from CoCo import CoCoData
from itertools import groupby
from operator import itemgetter

def _get_redis():
    if os.environ.get('REDISTOGO_URL'):
        url = urlparse.urlparse(os.environ.get('REDISTOGO_URL'))
        r = redis.Redis(host=url.hostname, port=url.port, password=url.password)
    #LOCAL
    else:
        r = redis.Redis(host=HOST, port=PORT)

    return r


def process_logs(EXPERIMENT_ID):
    r = _get_redis()

    DATA_FOLDER = './experiment_data/' + str(EXPERIMENT_ID) + '/'
    experiment = 'log:test_pop:' + str(EXPERIMENT_ID)

    data = [ast.literal_eval(i) for i in r.lrange(experiment, 0, -1)]
    data.reverse()

    #IF not exisits
    try:
        os.makedirs(DATA_FOLDER)
    except OSError:
        pass
    with open(DATA_FOLDER+experiment+'.json', 'w') as f:
        json.dump(data, f)


    grp_benchmark = itemgetter("benchmark","dim")
    grp_instance = itemgetter("benchmark","instance")
    result = []
    new_info = True
    for dim_key, benchmark_group in groupby(data, grp_benchmark):
        #Create folder if not exisits
        folder = DATA_FOLDER + '/F' + str(dim_key[0])
        try:
            os.makedirs(folder)
        except OSError:
            pass

        indexfile = DATA_FOLDER + '%s.info' % ( '/F' + str(dim_key[0]))

        # Create files
        filename = '%s-%02d_f%s_DIM%d' % (str(EXPERIMENT_ID), 0,
                                          str(dim_key[0]), dim_key[1])
        datafile =  folder+'/' + filename + '.tdat'
        hdatafile = folder+'/' + filename + '.dat'

        print "F" + str(dim_key[0]) + " Dimension:" + str(dim_key[1])

        comment = "% EvoSpace: Pool Based Algorithm see info in root folder"
        if new_info:
            info = """funcId = %s, DIM = %d, Precision = 1.000e-08, algId = 'EvoSpace'\n%s\nF%s/%s.dat, """ % \
               (str(dim_key[0]), dim_key[1], comment, dim_key[0],filename)
            new_info = False
        else:
            info = """\nfuncId = %s, DIM = %d, Precision = 1.000e-08, algId = 'EvoSpace'\n%s\nF%s/%s.dat, """ % \
                   (str(dim_key[0]), dim_key[1], comment, dim_key[0], filename)


        f = open(indexfile, 'a')
        f.writelines(info)

        f.close()
        new_instance = True

        for instance_key,benchmark in groupby(benchmark_group, grp_instance):
            print  " Instance:" + str(instance_key[1])


            coco = CoCoData(dim_key[1], function= dim_key[0], instance= instance_key[1] )
            index = 0
            total = 0
            buffr = []
            hbuffr =[]

            for row in benchmark:
                data_row = []
                row_id=0
                for e in row['evals']:
                    # We have to change this to a more practical solution

                    num_evals = row['params']['sample_size']

                    if len(e) >= 4:
                        num_evals = e[3]


                    data_row.append((e[1], row['algorithm'], e[0],num_evals, e[1],row['fopt'], '%+10.9e'% ( e[1]-row['fopt']),e[2]))
                    row_id+=1
                data_row.sort(reverse=True)
                for r in data_row:
                    coco.evalfun(*r[1:],buffr=buffr,hbuffr=hbuffr)

            if buffr:
                f = open(datafile, 'a')
                f.write('%% function evaluation | noise-free fitness - Fopt'
                        ' (%13.12e) | best noise-free fitness - Fopt | measured '
                        'fitness | best measured fitness | x1 | x2...\n' % row['fopt']
                        )


                f.writelines(buffr)

                f.close()
            if hbuffr:
                f = open(hdatafile, 'a')
                f.write('%% function evaluation | noise-free fitness - Fopt'
                        ' (%13.12e) | best noise-free fitness - Fopt | measured '
                        'fitness | best measured fitness | x1 | x2...\n' % row['fopt']
                        )
                f.writelines(hbuffr)
                f.close()


            last = buffr[-1].split(" ")






            f = open(indexfile, 'a')
            if new_instance:
                f.write('%s:%d|%.1e' % (instance_key[1],int(last[0]), float(last[1])))
                new_instance = False
            else:
                f.write(', %s:%d|%.1e' % (instance_key[1], int(last[0]), float(last[1])))

            f.close()
    return DATA_FOLDER



