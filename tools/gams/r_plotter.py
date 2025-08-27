from pathlib import Path
from rpy2 import rinterface_lib
from rpy2.robjects import pandas2ri, FactorVector
from rpy2.robjects.packages import importr
import rpy2.robjects as robjects
from rpy2.robjects.packages import STAP

Rplus = robjects.r['+']

class rPlotter:
    grDevices = importr('grDevices')
    base = importr('base')
    gg = importr('ggplot2')
    stats = importr('stats')
    null_value = robjects.rinterface.NULL
    available_scripts = {x.stem: x for x in Path(__file__).parent.resolve().glob('*.R')}

    def __init__(self) -> None:
        path = Path(__file__).parent / "general.R"
        self.r_src = self.load_src(path)

    @classmethod
    def load_src(cls, source):
        if source in cls.available_scripts:
            source = cls.available_scripts[source]

        with open(source, 'r') as f:
            inpt = f.read()

        return STAP(inpt, "str")

    @classmethod
    def save_workspace(cls, path):
        cls.base.save_image(str(path))

    def convert_to_rdf(self, df):
        context = self.context()
        with context():
            return pandas2ri.py2rpy(df)

    @classmethod
    def convert_to_df(cls, rdf):
        context = cls.context()
        with context():
            df = robjects.conversion.get_conversion().rpy2py(rdf)

        return df

    @classmethod
    def change_col_to_factor(cls, r_df, col):
        col_index = list(r_df.colnames).index(col)
        col_vals = FactorVector(r_df.rx2(col))
        r_df[col_index] = col_vals

    @classmethod
    def gr_plot(cls, filename, plot_object, y_limit_change=None):
        cls.grDevices.png(filename, width=1600, height=1600) # pylint: disable=no-member)
        if y_limit_change:
            plot_object = Rplus(plot_object, cls.gg.ylim(y_limit_change))

        cls.base.plot(plot_object)
        cls.grDevices.dev_off() # pylint: disable=no-member

    def context(self):
        return (robjects.default_converter + pandas2ri.converter).context

    @classmethod
    def capture_rpy2_output(cls, errorwarn_callback=None, print_callback=None):
        '''Prevent R output being written to console, for clean logging'''
        if not print_callback:
            print_callback = lambda x: None

        if not errorwarn_callback:
            errorwarn_callback = lambda x: None

        rinterface_lib.callbacks.consolewrite_print = print_callback
        rinterface_lib.callbacks.consolewrite_warnerror = errorwarn_callback
