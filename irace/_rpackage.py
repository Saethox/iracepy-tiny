from rpy2.robjects.packages import importr, PackageNotInstalledError

try:
    _irace = importr("irace")
except PackageNotInstalledError as e:
    raise PackageNotInstalledError(
        'The R package irace needs to be installed for this python binding to work. '
        'Consider running `Rscript -e "install.packages(\'irace\', repos=\'https://cloud.r-project.org\')"`'
        ' in your shell. '
        'See more details at https://github.com/mLopez-Ibanez/irace#quick-start') from e
