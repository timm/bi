#!/opt/local/bin/python2.6 

import matplotlib
matplotlib.interactive( True )
matplotlib.use( 'WXAgg' )
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
import matplotlib.pyplot as plt
from matplotlib import cm, colors
import numpy as num
import wx
import wxmpl
from arff import *
from instance import *
from quadrant import *
from util import *
from copy import deepcopy
from scipy import linspace, polyval, polyfit, sqrt, stats, randn
from which2 import *
from gridclus2 import *

class InstanceDialog(wx.Dialog):
    def __init__(self, parent, id, title, headers, you_are_here):
        wx.Dialog.__init__(self, parent, id, title, size=(250, 750))

        self.you_are_here = you_are_here
        self.parent = parent
        
        wx.StaticBox(self, -1, 'Update Information', (5, 5), size=(240, 750))
        self.text_ctrls = []
        for i in range(len(headers)):
            wx.StaticText(self, -1, str(headers[i]), (15, (i+1)*40))
            text_ctrl = wx.TextCtrl(self, -1, str(float(you_are_here.datum[i])), (90, (i+1)*40), (60, -1))
            self.text_ctrls.append(text_ctrl)
        wx.Button(self, 1, 'Ok', (160, 715), (60, -1))

        self.Bind(wx.EVT_BUTTON, self.OnClose, id=1)
        
        self.Centre()
        self.ShowModal()
        self.Destroy()
        
    def OnClose(self, event):
        for i in range(len(self.text_ctrls)):
            self.you_are_here.datum[i] = float(self.text_ctrls[i].GetValue())
        self.parent.updateYouAreHere(self.you_are_here)
        self.Close()

class ContrastDialog(wx.Dialog):
    def __init__(self, parent, id, title, rlist1, rlist2):
        wx.Dialog.__init__(self, parent, id, title, size=(500,500))

        self.parent = parent

        for i in range(1):
            wx.StaticText(self, -1, rlist1[i].describe(), (15, i*40))

        for i in range(1):
            wx.StaticText(self, -1, rlist2[i].describe(), (265, i*40))
            
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=1)

        self.Centre()
        self.ShowModal()
        self.Destroy()
        
    def OnClose(self, event):
        self.Close()        

class PlotPanel (wxmpl.PlotPanel):
    def __init__( self, parent, headers, color=None, dpi=None, **kwargs ):
        from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
        from matplotlib.figure import Figure

        self.overlay = False
        self.trend = False

        if 'id' not in kwargs.keys():
            kwargs['id'] = wx.ID_ANY
        if 'style' not in kwargs.keys():
            kwargs['style'] = wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Panel.__init__( self, parent, **kwargs )

        self.figure = Figure( None, dpi )
        self.canvas = FigureCanvasWxAgg( self, -1, self.figure )
        self.canvas.mpl_connect('button_release_event', self.on_release)
        
        self.SetColor( color )
        
        self.hs0 = wx.GridSizer(rows=20, cols=2, vgap=6, hgap=6)
        self.hs1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.hs0, flag=wx.EXPAND)
        self.sizer.Add(self.canvas, wx.EXPAND)
        self.sizer.Add(self.hs1, flag=wx.EXPAND)
        self.add_toolbar()
        self.SetSizer(self.sizer)
        
        self._SetSize()
        self.draw()

        self._resizeflag = False

        self.Bind(wx.EVT_IDLE, self._onIdle)
        self.Bind(wx.EVT_SIZE, self._onSize)
        
    def add_toolbar(self):
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()
        if wx.Platform == '__WXMAC__':
            # Mac platform (OSX 10.3, MacPython) does not seem to cope with
            # having a toolbar in a sizer. This work-around gets the buttons
            # back, but at the expense of having the toolbar at the top
            self.SetToolBar(self.toolbar)
        else:
            # On Windows platform, default window size is incorrect, so set
            # toolbar width to figure width.
            tw, th = self.toolbar.GetSizeTuple()
            fw, fh = self.canvas.GetSizeTuple()
            # By adding toolbar in sizer, we are able to put it at the bottom
            # of the frame - so appearance is closer to GTK version.
            # As noted above, doesn't work for Mac.
            self.toolbar.SetSize(wx.Size(fw, th))
        self.sizer.Add(self.toolbar, 0, wx.TOP | wx.RIGHT)
        # update the axes menu on the toolbar
        self.toolbar.update()
            
    def SetColor( self, rgbtuple=None ):
        if rgbtuple is None:
            rgbtuple = wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ).Get()
        clr = [c/255. for c in rgbtuple]
        self.figure.set_facecolor( clr )
        self.figure.set_edgecolor( clr )
        self.canvas.SetBackgroundColour( wx.Colour( *rgbtuple ) )

    def _onSize( self, event ):
        self._resizeflag = True

    def _onIdle( self, evt ):
        if self._resizeflag:
            self._resizeflag = False
            self._SetSize()

    def _SetSize( self ):
        pixels = tuple( self.parent.GetClientSize() )
        self.SetSize( pixels )
        self.canvas.SetSize( pixels )
        self.figure.set_size_inches( float( pixels[0] )/self.figure.get_dpi(),
                                     float( pixels[1] )/self.figure.get_dpi() )

    def on_release(self, event): pass
    def draw(self): pass
    def draw_trends(self, event): pass
    def draw_overlays(self, event): pass
    def color_quadrants(self, quadrants, color): pass
    def onAbout(self, event): pass
    def YouAreHere(self, event): pass
    def updateYouAreHere(self, you_are_here): pass
    def contrastSet(self, event): pass

def make_n_colors(cmap_name, n):
    cmap = cm.get_cmap(cmap_name, n)
    return cmap(np.arange(n))

def TimeToQuit(event):
    sys.exit(0)

if __name__ == '__main__':
    class DemoPlotPanel (PlotPanel):
        """Plots several lines in distinct colors."""
        def __init__( self, parent, instances, quadrants, clusters, headers, ic, **kwargs ):
            self.parent = parent
            self.instances = instances
            self.quadrants = quadrants
            self.headers = headers
            self.ic = ic
            self.you_are_here = random_element(self.instances)
            self.instances.remove(self.you_are_here)
            self.contrast = False
            self.contrast_quads = []
            self.clusters = clusters

            # initiate plotter
            PlotPanel.__init__( self, parent, headers, **kwargs )
            self.SetColor( (255,255,255) )

        def draw( self ):
            """Draw data."""
            if not hasattr(self, 'subplot'):
                self.subplot = self.figure.add_subplot(111)

            x = num.array([inst.coord.x for inst in self.instances])
            y = num.array([inst.coord.y for inst in self.instances])

            sets = list(set(transpose(arff.data)[0]))

            print sets[0], "blue"
            print sets[1], "red"
            print sets[2], "green"

            for inst in self.instances:
                if inst.datum[0] == sets[0]:
                    self.subplot.plot(inst.coord.x,inst.coord.y, "o", markerfacecolor="blue", markersize=3, alpha=0.5)
                elif inst.datum[0] == sets[1]:
                    self.subplot.plot(inst.coord.x,inst.coord.y, "o", markerfacecolor="red", markersize=3, alpha=0.5)
                elif inst.datum[0] == sets[2]:
                    self.subplot.plot(inst.coord.x,inst.coord.y, "o", markerfacecolor="green", markersize=3, alpha=0.5)
                    """
                elif inst.datum[0] == sets[3]:
                    self.subplot.plot(inst.coord.x,inst.coord.y, "o", markerfacecolor="yellow", markersize=3, alpha=0.5)
                elif inst.datum[0] == sets[4]:
                    self.subplot.plot(inst.coord.x,inst.coord.y, "o", markerfacecolor="orange", markersize=3, alpha=0.5)
                elif inst.datum[0] == sets[5]:
                    self.subplot.plot(inst.coord.x,inst.coord.y, "o", markerfacecolor="purple", markersize=3, alpha=0.5)
                    """
            self.subplot.plot(self.you_are_here.coord.x, self.you_are_here.coord.y, "ro", markersize=10)
            
            for quadrant in self.quadrants:
                xmin = quadrant.xmin
                xmax = quadrant.xmax
                ymin = quadrant.ymin
                ymax = quadrant.ymax
                self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor='white', visible=True, linewidth=0)

        def on_release(self, event):
            if self.contrast:
                print "X: ", event.xdata
                print "Y: ", event.ydata

                if len(self.contrast_quads) < 2:
                    for cluster in self.clusters:
                        for quadrant in cluster.quadrants:
                            xmin = quadrant.xmin
                            xmax = quadrant.xmax
                            ymin = quadrant.ymin
                            ymax = quadrant.ymax
                            if event.xdata <= xmax and event.xdata >= xmin and event.ydata <= ymax and event.ydata >= ymin:
                                self.contrast_quads.append(cluster)
                if len(self.contrast_quads) == 2:
                    print "You've selected two contrast clusters!"
                    ContrastDialog(self, -1, 'Contrast Dialog', which2n(self.headers, discretize(self.contrast_quads[0].datums())), which2n(self.headers, discretize(self.contrast_quads[1].datums())))
                        #ContrastDialog(self, -1, 'Contrast Dialog', [], [])
                else:                    
                    self.contrast_quads = []
                    for cluster in self.clusters:
                        for quadrant in cluster.quadrants:
                            xmin = quadrant.xmin
                            xmax = quadrant.xmax
                            ymin = quadrant.ymin
                            ymax = quadrant.ymax
                            if event.xdata <= xmax and event.xdata >= xmin and event.ydata <= ymax and event.ydata >= ymin:
                                self.contrast_quads.append(cluster)                    

        def onAbout(self, event):
            dlg = wx.MessageDialog(self.parent, "About information.",
                                  "About Me", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        def contrastSet(self, event):
            """
            if self.contrast:
                print "End contrasting!"
                self.contrast = False
            else:
                print "Begin contrasting!"
                self.contrast = True
            """
            dall = ic.datums()
            rall = which2n(arff.headers, dall)
            print "ALL done."
            cluster_rules = []
            
            for cluster in self.clusters:
                print len(cluster.datums())
                if len(cluster.datums()) < 20:
                    cluster_rules.append([])
                else:
                    cluster_rules.append(which2n(arff.headers, cluster.datums()))
                    print "C%d done, size=%d." % (clusters.index(cluster), len(cluster.datums()))
                    
            grid = {}
            for header in self.headers[0:-1]:
                for value in list(set(transpose(dall)[self.headers.index(header)])):
                    grid[(header, value)] = []
                    
            for rule in rall[0:19]:
                for thisors in rule.ands:
                    for value in thisors.values:
                        if "ALL" not in grid[(thisors.forr, value)]:
                            grid[(thisors.forr, value)].append("ALL")
                            
            for crules in cluster_rules:
                for rule in crules[0:19]:
                    for thisors in rule.ands:
                        for value in thisors.values:
                            if "C%d" % cluster_rules.index(crules) not in grid[(thisors.forr, value)]:
                                grid[(thisors.forr, value)].append("C%d" % cluster_rules.index(crules))

            for derp in grid:
                print derp, grid[derp]
                
        def updateYouAreHere(self, you_are_here):
            self.you_are_here = you_are_here

            a = distance(self.ic.west, self.you_are_here.datum)
            b = distance(self.ic.east, self.you_are_here.datum)
            c = distance(self.ic.west, self.ic.east)
            x = (b**2 - c**2 - a**2) / (-2 * c)
            y = math.sqrt(a**2 - x**2)

            x = x / self.ic.max_x
            y = y / self.ic.max_y
            
            x = math.log(x + 0.0001)
            y = math.log(y + 0.0001)

            self.you_are_here.coord.x = x
            self.you_are_here.coord.y = y
            
            xlim = self.subplot.get_xlim()
            ylim = self.subplot.get_ylim()
            self.subplot.clear()
            self.subplot.set_xlim(xlim)
            self.subplot.set_ylim(ylim)

            x = num.array([inst.coord.x for inst in self.instances])
            y = num.array([inst.coord.y for inst in self.instances])

            self.subplot.plot(x,y, "o", markersize=3, alpha=0.5)

            self.subplot.plot(self.you_are_here.coord.x, self.you_are_here.coord.y, "ro", markersize=10)

            if self.overlay == True:
                effort = [cluster.cmedian() for cluster in self.clusters]
                range_length = int(len(effort)/8)
                
                effort = sorted(effort)
                
                range1 = effort[range_length]
                range2 = effort[range_length*2]
                range3 = effort[range_length*3]
                range4 = effort[range_length*4]
                range5 = effort[range_length*5]
                range6 = effort[range_length*6]
                range7 = effort[range_length*7]
                range8 = effort[-1]
                
                greens = make_n_colors(cm.Greens_r, 80)
                reds = make_n_colors(cm.Reds, 240)
                
                for cluster in self.clusters:
                    for quadrant in cluster.quadrants:
                        xmin = quadrant.xmin
                        xmax = quadrant.xmax
                        ymin = quadrant.ymin
                        ymax = quadrant.ymax
                        if cluster.cmedian() < range1:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=greens[0], visible=True, linewidth=0)
                        elif cluster.cmedian() < range2:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=greens[19], visible=True, linewidth=0)                    
                        elif cluster.cmedian() < range3:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=greens[39], visible=True, linewidth=0)                    
                        elif cluster.cmedian() < range4:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=greens[59], visible=True, linewidth=0)                    
                        elif cluster.cmedian() < range5:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=reds[60], visible=True, linewidth=0)                    
                        elif cluster.cmedian() < range6:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=reds[120], visible=True, linewidth=0)                    
                        elif cluster.cmedian() < range7:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=reds[180], visible=True, linewidth=0)                    
                        else:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=reds[239], visible=True, linewidth=0)                    
            else:
                for quadrant in self.quadrants:
                    xmin = quadrant.xmin
                    xmax = quadrant.xmax
                    ymin = quadrant.ymin
                    ymax = quadrant.ymax
                    self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor='white', visible=True, linewidth=0)
            #self.subplot.draw(self.subplot)

        def YouAreHere(self, event):
            InstanceDialog(self, -1, 'You Are Here', self.headers, self.you_are_here)

        def draw_trends(self, event):
            xlim = self.subplot.get_xlim()
            ylim = self.subplot.get_ylim()
            self.subplot.clear()
            self.subplot.set_xlim(xlim)
            self.subplot.set_ylim(ylim)

            one = random_element(self.instances)
            two = random_element(self.instances)
            three = random_element(self.instances)
            four = random_element(self.instances)            

            x = num.array([one.coord.x, two.coord.x, three.coord.x, four.coord.x])
            y = num.array([one.coord.y, two.coord.y, three.coord.y, four.coord.y])

            x2 = num.array([inst.coord.x for inst in self.instances])
            y2 = num.array([inst.coord.y for inst in self.instances])
            
            (ar,br)=polyfit( x, y, 1)
            xr = polyval([ar,br], x)
            self.subplot.plot(x,y, "ro", x, xr, 'b.-', markersize=6)
            self.subplot.plot(x2, y2, "o", markersize=3, alpha=0.5)

            if self.overlay == True:
                effort = [cluster.cmedian() for cluster in self.clusters]
                range_length = int(len(effort)/8)
                
                effort = sorted(effort)
                
                range1 = effort[range_length]
                range2 = effort[range_length*2]
                range3 = effort[range_length*3]
                range4 = effort[range_length*4]
                range5 = effort[range_length*5]
                range6 = effort[range_length*6]
                range7 = effort[range_length*7]
                range8 = effort[-1]
                
                greens = make_n_colors(cm.Greens_r, 80)
                reds = make_n_colors(cm.Reds, 240)
                
                for cluster in self.clusters:
                    for quadrant in cluster.quadrants:
                        xmin = quadrant.xmin
                        xmax = quadrant.xmax
                        ymin = quadrant.ymin
                        ymax = quadrant.ymax
                        if cluster.cmedian() < range1:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=greens[0], visible=True, linewidth=0)
                        elif cluster.cmedian() < range2:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=greens[19], visible=True, linewidth=0)                    
                        elif cluster.cmedian() < range3:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=greens[39], visible=True, linewidth=0)                    
                        elif cluster.cmedian() < range4:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=greens[59], visible=True, linewidth=0)                    
                        elif cluster.cmedian() < range5:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=reds[60], visible=True, linewidth=0)                    
                        elif cluster.cmedian() < range6:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=reds[120], visible=True, linewidth=0)                    
                        elif cluster.cmedian() < range7:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=reds[180], visible=True, linewidth=0)                    
                        else:
                            self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=reds[239], visible=True, linewidth=0)                
            else:
                for quadrant in self.quadrants:
                    xmin = quadrant.xmin
                    xmax = quadrant.xmax
                    ymin = quadrant.ymin
                    ymax = quadrant.ymax
                    self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor='white', visible=True, linewidth=0)
            
            self.subplot.draw()

        def draw_overlays(self, event):
            if self.overlay == False:
                self.overlay = True
                
            xlim = self.subplot.get_xlim()
            ylim = self.subplot.get_ylim()
            self.subplot.clear()
            self.subplot.set_xlim(xlim)
            self.subplot.set_ylim(ylim)

            #x = num.array([inst.coord.x for inst in self.instances])
            #y = num.array([inst.coord.y for inst in self.instances])            
            #self.subplot.plot(x, y, "o", markersize=3, alpha=0.5)

            #self.subplot.plot(self.you_are_here.coord.x, self.you_are_here.coord.y, "ro", markersize=10)

            effort = [cluster.cmedian() for cluster in self.clusters]
            range_length = int(len(effort)/8)
            
            effort = sorted(effort)
            
            range1 = effort[range_length]
            range2 = effort[range_length*2]
            range3 = effort[range_length*3]
            range4 = effort[range_length*4]
            range5 = effort[range_length*5]
            range6 = effort[range_length*6]
            range7 = effort[range_length*7]
            range8 = effort[-1]
            
            greens = make_n_colors(cm.Greens_r, 80)
            reds = make_n_colors(cm.Reds, 240)
            
            for cluster in self.clusters:
                for quadrant in cluster.quadrants:
                    xmin = quadrant.xmin
                    xmax = quadrant.xmax
                    ymin = quadrant.ymin
                    ymax = quadrant.ymax
                    if cluster.cmedian() < range1:
                        self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=greens[0], visible=True, linewidth=0)
                    elif cluster.cmedian() < range2:
                        self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=greens[19], visible=True, linewidth=0)                    
                    elif cluster.cmedian() < range3:
                        self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=greens[39], visible=True, linewidth=0)                    
                    elif cluster.cmedian() < range4:
                        self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=greens[59], visible=True, linewidth=0)                    
                    elif cluster.cmedian() < range5:
                        self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=reds[60], visible=True, linewidth=0)                    
                    elif cluster.cmedian() < range6:
                        self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=reds[120], visible=True, linewidth=0)                    
                    elif cluster.cmedian() < range7:
                        self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=reds[180], visible=True, linewidth=0)                    
                    else:
                        self.subplot.bar(xmin, (ymax-ymin), width=(xmax-xmin), bottom=ymin, facecolor=reds[239], visible=True, linewidth=0)                
                        
            for cluster in self.clusters:
                xmin = cluster.quadrants[0].xmin
                xmax = cluster.quadrants[0].xmax
                ymin = cluster.quadrants[0].ymin
                ymax = cluster.quadrants[0].ymax
                self.subplot.text((xmin+xmax)/2, (ymin+ymax)/2, "%d" % clusters.index(cluster), ha="center", size=18, weight="bold")
                
            self.subplot.draw()            
                    
    #arff = Arff(["data/jedit/jedit4.2.arff", "data/xerces/xerces1.4.arff", "data/lucene/lucene2.4.arff", "data/velocity/velocity1.6.arff", "data/xalan/xalan2.7.arff", "data/tomcat.arff"])
    arff = Arff(["data/lucene/lucene2.0.arff", "data/velocity/velocity1.4.arff", "data/xalan/xalan2.7.arff"])
    #dc = DataCollection(discretize(arff.data, 7))
    dc = DataCollection(arff.data)
    ic = InstanceCollection(dc)
    ic.normalize_coordinates()

    trainXY = log_y(log_x(deepcopy(ic.instances)))
    quadrants = QuadrantTree(trainXY).leaves()
    clusters = GRIDCLUS(quadrants)

    app = wx.PySimpleApp( 0 )
    frame = wx.Frame( None, wx.ID_ANY, 'WxPython and Matplotlib', size=(768, 512) )
    panel = DemoPlotPanel( frame, trainXY, quadrants, clusters, arff.headers, ic)

    menu = wx.Menu()
    menu.Append(wx.ID_ABOUT, "&About",
                "Display an about message.")
    menu.AppendSeparator()
    menu.Append(2012, "&Trends",
                "Project trends for several points.")
    menu.AppendSeparator()
    menu.Append(2013, "&Overlays",
                "Summarize quadrant scores with color map.")
    menu.AppendSeparator()
    menu.Append(2014, "&You Are Here",
                "Update you are here information.")
    menu.AppendSeparator()
    menu.Append(2015, "&Contrast",
                "Display contrast set for two selected regions.")
    
    menu.AppendSeparator()    
    menu.Append(wx.ID_EXIT, "E&xit", "Terminate the program")

    menuBar = wx.MenuBar()
    menuBar.Append(menu, "&File");
    
    frame.SetMenuBar(menuBar)
    wx.EVT_MENU(frame, wx.ID_ABOUT, panel.onAbout)
    wx.EVT_MENU(frame, wx.ID_EXIT, TimeToQuit)
    wx.EVT_MENU(frame, 2012, panel.draw_trends)
    wx.EVT_MENU(frame, 2013, panel.draw_overlays)
    wx.EVT_MENU(frame, 2014, panel.YouAreHere)
    wx.EVT_MENU(frame, 2015, panel.contrastSet)
    
    frame.Show()
    app.MainLoop()
