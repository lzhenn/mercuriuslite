from . import const
import matplotlib, os, datetime
import numpy as np
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
print_prefix='lib.painter>>'


def fast_plot(oculus):
    # Time series
    ticker=oculus.ticker
    if oculus.model_name in ['plainhist']:
        nday_series=np.arange(oculus.determin.shape[0])
        plt.plot(
            nday_series, oculus.prob.T, 
            linestyle='-', linewidth=0.5, alpha=0.5,color='grey')
        plt.plot(
            nday_series, oculus.determin, label='Deterministic', 
            linestyle='-', linewidth=3, color='blue')
    
    # Scatter plot
    elif oculus.model_name in ['svpdf']:
        # Start with a square Figure.
        fig = plt.figure(figsize=(6, 6))
        # Add a gridspec with two rows and two columns and a ratio of 1 to 4 between
        # the size of the marginal axes and the main axes in both directions.
        # Also adjust the subplot parameters for a square plot.
        gs = fig.add_gridspec(1, 2,  width_ratios=(3,1), 
                        left=0.1, right=0.9, bottom=0.1, top=0.9,
                        wspace=0.05, hspace=0.05)
        # Create the Axes.
        ax = fig.add_subplot(gs[0, 0])
        #ax_histx = fig.add_subplot(gs[0, 0], sharex=ax)
        ax_histy = fig.add_subplot(gs[0, 1], sharey=ax)

        # Draw the scatter plot and marginals.
        x,y=oculus.prob[:,1], oculus.prob[:,0]
        ybase=oculus.baseline
        x0, y0 =oculus.determin[1][0], oculus.determin[0]
        scatter_hist(x, y, ybase, ax, ax_histy)
        # -----------------set ax-----------------
        ax.scatter(
            x0, y0, marker='*', color='blue',
            s=100, label='Deterministic')
        ax.hlines(y=0.0, xmin=x.min(), xmax=x.max(), 
            linewidth=1, color='red', linestyles='--')
        # Add a label to the point
        ax.text(x0, y0, '({:.2%}, {:.2%})'.format(x0, y0), fontsize=const.MID_SIZE)
        
        info_text=get_info(y, ybase)
        ax.text(x.min(), ybase.min(), info_text, fontsize=const.SM_SIZE)
        ax.xaxis.set_major_formatter(
            mtick.PercentFormatter(xmax=1, decimals=2))
        ax.yaxis.set_major_formatter(
            mtick.PercentFormatter(xmax=1, decimals=2))
        ax.legend(loc='upper right', fontsize=const.MID_SIZE)
        ax.set_xlabel(oculus.Xnames)
        ax.set_ylabel(f'{oculus.Ytgt_str} Return (%)')
        ax.tick_params(axis='x', labelrotation = 30)
        title=f'{oculus.model_name}: {ticker} Init:{oculus.pred_init_time.strftime("%Y-%m-%d")},'
        title=f'{title} Tgt:{oculus.Ytgt_str.split("_")[-1]}'
        ax.set_title(title)
        
        # ---------set ax_histy----------
        ax_histy.hlines(y=0.0, xmin=0, xmax=5, linewidth=1, color='red')
        ax_histy.hlines(y=ybase.mean(), xmin=0, xmax=1, linewidth=2, color='black')       
        
    plt.show()
    plt.savefig(os.path.join('./fig/', oculus.model_name+'.'+oculus.ticker+'.png'), 
        bbox_inches='tight', dpi=const.DPI)

def scatter_hist(x, y, ybase, ax, ax_histy):
    # no labels
    ax_histy.tick_params(axis="y", labelleft=False)

    # the scatter plot:
    ax.scatter(x, y, marker='.', alpha=0.3, color='blue',
        label='Prob')

    #ax_histx.hist(x, bins=50)
    ax_histy.hist(y, bins=50, orientation='horizontal', 
        density=True, color='dodgerblue')
    ax_histy.hist(ybase, bins=50, orientation='horizontal', 
        density=True, alpha=0.5, color='grey')

def get_info(y, ybase):
    info='Win: {:.1%} ({:.1%})\n'.format((y>0).sum()/len(y),(ybase>0).sum()/len(ybase))
    info=info+'Return: {:.2%} ({:.2%})'.format(y.mean(), ybase.mean())
    return info