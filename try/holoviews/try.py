import pandas as pd
import nysol.mcmd as nm
import pprint
pp = pprint.PrettyPrinter(indent=4)

from bokeh.palettes import Dark2_5 as palette
from bokeh.palettes import cividis,brewer,viridis
import itertools

k = "表示時間"
f = "S1"
c = "min,mean,max"
df = pd.read_csv('./data/反復波形図1.csv')
i = df.values.tolist()
i.insert(0,list(df.columns))



fs = None
fs <<= nm.msummary(i=i, k=k, f=f, c=c).writelist(dtype="表示時間:float",header=True)
fs = fs.run()

name=fs.pop(0)
df=pd.DataFrame(fs,columns=name)
z = df.sort_values(by = '表示時間')

pp.pprint(z)