from  utils import * 
import numpy as np 
from pymc import *


data = readtabledict('srrs2.dat', delimiter = ',', quotechar='"', skipinitialspace = True)

cty_data= readtabledict('cty.dat', delimiter = ',', quotechar='"', skipinitialspace = True)
def dictmap(f, d):
    return dict((k, f(v)) for k, v in d.iteritems())

mn = data['state'] == 'MN'
data = dictmap(lambda v: v[mn], data)



radon = data['activity']
floor = data['floor']
lradon = np.log(np. where(radon ==0, .1, radon))
fips = data['stfips']*1000 + data['cntyfips']

cty_data['fips'] = cty_data['stfips']*1000 + cty_data['ctfips']

ufull = cty_data['Uppm'][searchsorted(cty_data['fips'], fips)]


stfips,ctfips,st,cty,lon,lat,Uppm = readtable('cty.dat', delimiter = ',' )

ufips = np.unique(fips)
n = ufips.shape[0]
group = np.searchsorted(ufips, fips)
obs_means = np.array([np.mean(lradon[fips == fip]) for fip in np.unique(fips)])



start = {'groupmean' : np.mean(obs_means )[None],
         'groupsd' : np.std(obs_means)[None], 
         'sd' : np.std(lradon)[None], 
         'means' : obs_means,
         'floor_m' : np.array([0.]),
         }
model = Model(test_point= start)
Var = model.Var
Data = model.Data

groupmean = Var('groupmean', Normal(0, (10)**-2))

#as recommended by "Prior distributions for variance parameters in hierarchical models"
groupsd = Var('groupsd', Uniform(0,10))

sd = Var('sd', Uniform(0, 10))

floor_m = Var('floor_m', Normal(0, 5.** -2))

means = Var('means', Normal(groupmean, groupsd ** -2), n)


#the gradient of indexing into an array is generally slow unless you have the experimental branch of theano
Data(lradon, Normal( floor*floor_m + means[group], sd**-2))

hess = np.diag(approx_hess(model, start))

step_method = hmc_step(model, model.vars, hess, .2, 1.0, is_cov = False)
#step_method = hmc_lowflip_step(model, model.vars, hess, .5, a = .5)

history, state, t = sample(3000, step_method, start)

print  " took: ", t