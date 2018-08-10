# -*- coding: utf-8 -*-

"""matplotlib task module."""

import os
import topcli

class MPLTask(topcli.TaskFrameUnit):

    def __init__(self, ctr, parent, url, argv, env):

        self.parser.add_argument('-f', metavar='figure creation', help='define a figure for plotting.')
        self.parser.add_argument('-t', '--title', metavar='title', action='append', help='title  plotting.')
        self.parser.add_argument('-p', '--plot', metavar='plot type', action='append', help='plot type for plotting.')
        self.parser.add_argument('-s', '--save', metavar='save', action='append', help='file path to save png image.')
        self.parser.add_argument('-x', '--xaxis', metavar='xaxis', action='append', help='axes function wrapper for x axis settings.')
        self.parser.add_argument('-y', '--yaxis', metavar='yaxis', action='append', help='axes function wrapper for y axis settings.')
        self.parser.add_argument('-z', '--zaxis', metavar='zaxis', action='append', help='axes function wrapper for z axis settings.')
        self.parser.add_argument('-g', action='store_true', help='grid for ax plotting.')
        self.parser.add_argument('-l', action='store_true', help='legend for ax plotting')
        self.parser.add_argument('--pages', metavar='pages', help='page settings.')
        self.parser.add_argument('--page-calc', metavar='page_calc', action='append', help='python code for manipulating data within page generation.')
        self.parser.add_argument('--pandas', metavar='pandas', action='append', help='pandas plots.')
        self.parser.add_argument('--legend', metavar='legend', action='append', help='plot legend')
        self.parser.add_argument('--grid', metavar='grid', action='append', help='grid for plotting.')
        self.parser.add_argument('--subplot', metavar='subplot', action='append', help='define subplot.')
        self.parser.add_argument('--figure', metavar='figure function', action='append', help='define Figure function.')
        self.parser.add_argument('--axes', metavar='axes', action='append', help='define Axes function.')
        self.parser.add_argument('--noshow', action='store_true', default=False, help='prevent showing plot on screen.')
        self.parser.add_argument('--version', action='version', version='matplotlib plotting task version 0.1.0')

        self.targs = self.parser.parse_args(argv)

        try:
            import matplotlib
            import matplotlib.pyplot
            self.env["matplotlib"] = self.env["mpl"] = matplotlib
            self.env["pyplot"] = self.env["plt"] = matplotlib.pyplot
        except ImportError as err:
            self.error_exit(str(err))

        try:
            import numpy
            self.env["numpy"] = self.env["np"] = numpy
        except ImportError as err:
            pass

        try:
            import pandas
            self.env["pandas"] = self.env["pd"] = pandas
        except ImportError as err:
            pass
        
    def perform(self):

        # pages setting
        if self.targs.pages:
            vargs, kwargs = self.teval_args(self.targs.pages)

            if vargs:
                self.env['num_pages'] = vargs[-1]
            else:
                self.env['num_pages'] = 1

            for key, value in kwargs.items():
                self.env[key] = value
        else:
            self.env['num_pages'] = 1

        # page iteration
        for idx in range(self.env['num_pages']):

            self.env['page_num'] = idx

            if self.targs.page_calc:
                for page_calc in self.targs.page_calc:
                    vargs, kwargs = self.teval_args(page_calc)
                    self.env.update(kwargs)

            # figure setting
            if self.targs.f:
                self.env['figure'] = self.teval('pyplot.figure(%s)'%self.targs.f)
            else:
                self.env['figure'] = self.env['pyplot'].figure()

            # plot axis
            if self.targs.subplot:
                for subplot_arg in self.targs.subplot:
                    # syntax: subplotname@funcargs
                    items, vargs, kwargs = self.teval_atargs(subplot_arg)

                    if len(items) == 1:
                        subpname = items[0]

                        if 'projection' in kwargs and kwargs['projection'] == '3d':
                             from mpl_toolkits.mplot3d import Axes3D
                             self.env['Axes3D'] = Axes3D
                        if vargs:
                            subplot = self.env['figure'].add_subplot(*vargs, **kwargs)
                        else:
                            subplot = self.env['figure'].add_subplot(111, **kwargs)
                
                        try:
                            self.env[subpname] = subplot
                        except Exception as err:
                            self.error_exit("syntax error from subplot name: %s"%subpname)
                    else:
                        self.error_exit("Only one axis name is allowed: %s"%subplot_arg)

            # page names
            if 'page_names' in self.env:
                page_names = self.env['page_names']
                if callable(page_names):
                    self.env['page_name'] = self.teval_func(page_names)
                else:
                    self.env['page_name'] = page_names[self.env['page_num']]
            else:
                self.env['page_name'] = 'page%d'%self.env['page_num']

            # execute figure functions
            if self.targs.figure:
                for fig_arg in self.targs.figure:

                    # syntax: funcname@funcargs
                    items, vargs, kwargs = self.teval_atargs(fig_arg)

                    if len(items) == 1:
                        getattr(self.env['figure'], items[0])(*vargs, **kwargs)
                    else:
                        self.error_exit("The synaxt error near '@': %s"%fig_arg)

            if self.targs.pandas:
                for pd_arg in self.targs.pandas:
                    # syntax: data@[plot@]funcargs
                    items, vargs, kwargs = self.teval_atargs(pd_arg)

                    if len(items) == 1:
                        data = self.teval(items[0])
                        plot = getattr(data, "plot")
                    elif len(items) == 2:
                        data = self.teval(items[0])
                        plot = getattr(data, "plot")
                        plot = getattr(plot, items[1])
                    else:
                        self.error_exit("The synaxt error near '@': %s"%pd_arg)

                    subp = plot(*vargs, **kwargs)
                    if "ax" not in self.env:
                        self.env['ax'] = subp

            elif not self.targs.subplot:
                self.env['ax'] = self.env['figure'].add_subplot(111)

            # plotting
            plots = []
            if self.targs.plot:
                for plot_arg in self.targs.plot:

                    # syntax: [axname@]funcname@funcargs
                    items, vargs, kwargs = self.teval_atargs(plot_arg)

                    if len(items) == 1:
                        axis = self.env["ax"]
                        funcname = items[0]
                    elif len(items) == 2:
                        axis = self.env[items[0]]
                        funcname = items[1]
                    else:
                        self.error_exit("The synaxt error near '@': %s"%plot_arg)

                    if hasattr(axis, funcname):
                        plot_handle = getattr(axis, funcname)(*vargs, **kwargs)

                        try:
                            for p in plot_handle:
                                plots.append(p)
                        except TypeError:
                            plots.append(plot_handle)
                    else:
                        # TODO: handling this case
                        pass

                    if funcname == 'pie':
                        axis.axis('equal')

            if 'plots' in self.env:
                self.env['plots'].extend(plots)
            else:
                self.env['plots'] = plots

            # title setting
            if self.targs.title:
                for title_arg in self.targs.title:
                    # syntax: [axname[,axname...]@]funcargs
                    items, vargs, kwargs = self.teval_atargs(title_arg)

                    if len(items) == 0:
                        axes = [self.env["ax"]]
                    elif len(items) == 1:
                        axes = [self.env[items[0]]]
                    else:
                        self.error_exit("The synaxt error near '@': %s"%title_arg)

                    for ax in axes:
                        ax.set_title(*vargs, **kwargs)

            # x-axis setting
            if self.targs.xaxis:
                for xaxis_arg in self.targs.xaxis:

                    # syntax: [axname@]funcname@funcargs
                    items, vargs, kwargs = self.teval_atargs(xaxis_arg)

                    if len(items) == 1:
                        axis = self.env["ax"]
                        funcname = "set_x"+items[0]
                    elif len(items) == 2:
                        axis = self.env[items[0]]
                        funcname = "set_x"+items[1]
                    else:
                        self.error_exit("The synaxt error near '@': %s"%xaxis_arg)

                    if hasattr(axis, funcname):
                        getattr(axis, funcname)(*vargs, **kwargs)
                    else:
                        # TODO: handling this case
                        pass

            # y-axis setting
            if self.targs.yaxis:
                for yaxis_arg in self.targs.yaxis:

                    # syntax: [axname@]funcname@funcargs
                    items, vargs, kwargs = self.teval_atargs(yaxis_arg)

                    if len(items) == 1:
                        axis = self.env["ax"]
                        funcname = "set_y"+items[0]
                    elif len(items) == 2:
                        axis = self.env[items[0]]
                        funcname = "set_y"+items[1]
                    else:
                        self.error_exit("The synaxt error near '@': %s"%yaxis_arg)

                    if hasattr(axis, funcname):
                        getattr(axis, funcname)(*vargs, **kwargs)
                    else:
                        # TODO: handling this case
                        pass

            # z-axis setting
            if self.targs.zaxis:
                for zaxis_arg in self.targs.zaxis:

                    # syntax: [axname@]funcname@funcargs
                    items, vargs, kwargs = self.teval_atargs(zaxis_arg)

                    if len(items) == 1:
                        axis = self.env["ax"]
                        funcname = "set_z"+items[0]
                    elif len(items) == 2:
                        axis = self.env[items[0]]
                        funcname = "set_z"+items[1]
                    else:
                        self.error_exit("The synaxt error near '@': %s"%zaxis_arg)

                    if hasattr(axis, funcname):
                        getattr(axis, funcname)(*vargs, **kwargs)
                    else:
                        # TODO: handling this case
                        pass

            # grid setting
            if self.targs.g:
                for key, value in self.env.items():
                    if isinstance(value, self.env['mpl'].axes.Axes):
                        value.grid()

            if self.targs.grid:
                for grid_arg in self.targs.grid:

                    # syntax: [axname@]funcargs
                    items, vargs, kwargs = self.teval_atargs(grid_arg)

                    if len(items) == 0:
                        axis = self.env["ax"]
                    elif len(items) == 1:
                        axis = self.env[items[0]]
                    else:
                        self.error_exit("The synaxt error near '@': %s"%grid_arg)

                    axis.grid(*vargs, **kwargs)

            # legend setting
            if self.targs.l:
                for key, value in self.env.items():
                    if isinstance(value, self.env['mpl'].axes.Axes):
                        value.legend()

            if self.targs.legend:
                for legend_arg in self.targs.legend:

                    # syntax: [axname@]funcargs
                    items, vargs, kwargs = self.teval_atargs(legend_arg)

                    if len(items) == 0:
                        axis = self.env["ax"]
                    elif len(items) == 1:
                        axis = self.env[items[0]]
                    else:
                        self.error_exit("The synaxt error near '@': %s"%legend_arg)

                    axis.legend(*vargs, **kwargs)

            # execute axes functions
            if self.targs.axes:
                for axes_arg in self.targs.axes:
                    # syntax: [axname@]funcname@funcargs
                    items, vargs, kwargs = self.teval_atargs(axes_arg)

                    if len(items) == 1:
                        axis = self.env["ax"]
                        funcname = items[0]
                    elif len(items) == 2:
                        axis = self.env[items[0]]
                        funcname = items[1]
                    else:
                        self.error_exit("The synaxt error near '@': %s"%axes_arg)

                    getattr(ax, funcname)(*vargs, **kwargs)

            elif not self.env['plots']:
                if self.targs.figure or self.targs.pandas:
                    pass
                elif self.env["D"]:
                    for d in self.env["D"]:
                        self.env["ax"].plot(d)
                else:
                    self.error_exit("There is no data to plot.")

            # saving an image file
            if self.targs.save:
                for save_arg in self.targs.save:
                    vargs, kwargs = self.teval_args(save_arg)

                    name = vargs.pop(0)

                    if self.env['num_pages'] > 1:
                        if os.path.exists(name):
                            if not os.path.isdir(name):
                                os.remove(name)
                                os.makedirs(name)
                        else:
                            os.makedirs(name)
                            
                        name = os.path.join(name, str(self.env['page_num'])+".pdf")
                        #root, ext = os.path.splitext(name)
                        #name = os.path.join(root, '%s-%d%s'%(self.env['page_num'], ext))

                    self.env["figure"].savefig(name, *vargs, **kwargs)

            #if self.env["B"]:
            #    self.env["B"].savefig(figure=self.env["figure"])

            # displyaing an image on screen
            if not self.targs.noshow:
                self.env['pyplot'].show()

            self.env["figure"].clear()
            self.env["pyplot"].close(self.env["figure"])
            del self.env['figure']

        return 0
