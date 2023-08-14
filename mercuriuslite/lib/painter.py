from . import const, utils, mathlib
import matplotlib, os, datetime
import numpy as np
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
print_prefix='lib.painter>>'


def draw_perform_fig(df, scheme_name,tgts,evaltb_dic):
    # Calculate the daily return rate

    # Calculate the maximum drawdown

    # Plot the three figures
    fig, ax = plt.subplots(nrows=3, sharex=True, figsize=(10,8))

    # ----------Upper plot: NAV timeseries
    port_colors=['blue', 'red', 'gold']
    ax[0].plot(df.index, df['accu_fund'], 
        label=f'AccuFund: {utils.fmt_value(df.iloc[-1]["accu_fund"])}', 
        color='red', linewidth=1)
    ax[0].plot(df.index, df['norisk_total_value'], 
        label=f'NoRiskV: {utils.fmt_value(df.iloc[-1]["norisk_total_value"])}', 
        color='green', linewidth=1)
    ax[0].plot(df.index, df['total_value'], 
        label=f'NAV: {utils.fmt_value(df.iloc[-1]["total_value"])}', 
        color='blue')
 
    ax[0].fill_between(
        df.index, df['cash'], 0, where=df['cash']>0, 
        color='green', alpha=0.3, 
        label=f'Cash ({utils.fmt_value(df.iloc[-1]["cash"]/df.iloc[-1]["total_value"],vtype="pct")})')
    df_accu=df['cash']
    for idx,tgt in enumerate(tgts):
        ax[0].fill_between(
            df.index, df[tgt+'_value']+df_accu, df_accu, 
            where=df_accu>0, color=port_colors[idx], alpha=0.3,
            label=f'{tgt} ({utils.fmt_value(df.iloc[-1][tgt+"_value"]/df.iloc[-1]["total_value"],vtype="pct")})')
        df_accu=df_accu+df[tgt+'_value']
    #ax[0].set_yscale('log')
    ax[0].set_ylabel('NAV')
    ax[0].legend(loc='upper left',fontsize=const.SM_SIZE)

    # ------------Middle plot: return rate
    ax[1].plot(df.index, df['fund_change']+1, 
               label=f'ARR ({utils.fmt_value(df.iloc[-1]["fund_change"],vtype="pct")})',
               color='red', linewidth=1)
    cagr_str=utils.fmt_value(mathlib.cagr(df.iloc[-1]['baseline_return']-1,len(df)),vtype="pct")
    ax[1].plot(df.index, df['baseline_return'], 
               label=f'Baseline ({utils.fmt_value(df.iloc[-1]["baseline_return"]-1,vtype="pct")}|{cagr_str})',
               color='orange', linewidth=1)
    cagr_str=utils.fmt_value(mathlib.cagr(df.iloc[-1]['accum_return']-1,len(df)),vtype="pct")
    ax[1].plot(df.index, df['accum_return'], 
               label=f'TWR ({utils.fmt_value(df.iloc[-1]["accum_return"]-1,vtype="pct")}|{cagr_str})', 
               color='blue')
    
    no_risk=df['norisk_total_value']/df['accu_fund']
    ax[1].plot(df.index, no_risk, 
               label=f'NoRisk ARR ({utils.fmt_value(no_risk[-1]-1,vtype="pct")})', 
               color='green', linewidth=1)
    
    ax[1].hlines(y=1.0, xmin=df.index[0], xmax=df.index[-1], 
            linewidth=1, color='grey', linestyles='--')
    ax[1].set_ylabel('Return Rate')
    ax[1].legend(loc='upper left',fontsize=const.SM_SIZE)

    # Lower plot: maximum drawdown
    ax[2].plot(df.index, -df['baseline_drawdown'], color='orange', linewidth=1, 
        label=f'Baseline (Max: {utils.fmt_value(-df["baseline_drawdown"].max(),vtype="pct")})')
    ax[2].fill_between(
        df.index, -df['baseline_drawdown'], 0, where=df['baseline_drawdown']>0, color='yellow', alpha=0.3)
   
    ax[2].plot(df.index, -df['drawdown'], alpha=0.5, 
               label=f'Drawdown (Max: {utils.fmt_value(-df["drawdown"].max(),vtype="pct")})', color='blue')
    ax[2].fill_between(
        df.index, -df['drawdown'], 0, where=df['drawdown']>0, color='blue', alpha=0.3)
    ax[2].legend(loc='lower left',fontsize=const.SM_SIZE)
    ax[2].set_ylabel('Drawdown')

    # Set the x-axis label and title
    plt.xlabel('Date')
    plt.suptitle('Portfolio Performance')

    # Show the plot
    plt.show()
    plt.savefig(os.path.join('./fig/', scheme_name+'.png'), 
        bbox_inches='tight', dpi=const.DPI)
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

def table_print(table):
    from tabulate import tabulate
    print(tabulate(
        table.items(),headers=['Metrics', 'Value'],tablefmt='fancy_grid'))