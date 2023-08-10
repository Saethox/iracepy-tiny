import rpy2.robjects.packages as rpackages
from rpy2.robjects.vectors import StrVector

if __name__ == '__main__':
    utils = rpackages.importr('utils')
    utils.chooseCRANmirror(ind=1)  # select the first mirror in the list

    packages = ['devtools', 'irace']
    missing_packages = [x for x in packages if not rpackages.isinstalled(x)]
    if len(missing_packages) > 0:
        utils.install_packages(StrVector(packages), verbose=True)
