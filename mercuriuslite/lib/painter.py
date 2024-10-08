from . import const, utils, mathlib
import matplotlib, os, datetime
import pandas as pd
import numpy as np
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
print_prefix='lib.painter>>'


def draw_perform_fig(
    df, tgts, fig_fn, 
    port_colors=['blue', 'red', 'purple', 'darkcyan', 'gold', 'grey', 'pink'],
    withbase=True, financing=False, leverage=False,att_dic={}):
    # Calculate the daily return rate


    # Plot the three figures
    fig, ax = plt.subplots(nrows=4, sharex=True, figsize=(12,12))
    fig.subplots_adjust(hspace=0)
    # ----------plot 0: Total Assets, NAV timeseries

    total_days=(df.index[-1]-df.index[0]).days+1
    ax[0].plot(df.index, df['accu_fund'], 
        label=f'AccuFund: {utils.fmt_value(df.iloc[-1]["accu_fund"],pos_sign=False)}', 
        color='black', linewidth=1)
    chg=utils.fmt_value(df.iloc[-1]["norisk_total_value"]-df.iloc[-1]["accu_fund"])
    ax[0].plot(df.index, df['norisk_total_value'], 
        label=f'NoRiskV: {utils.fmt_value(df.iloc[-1]["norisk_total_value"],pos_sign=False)} ({chg})', 
        color='lightgrey', linewidth=1.5)
    chg=utils.fmt_value(df.iloc[-1]["total_value"]-df.iloc[-1]["accu_fund"])
    ax[0].plot(df.index, df['total_value'], 
        label=f'Total Assets: {utils.fmt_value(df.iloc[-1]["total_value"], pos_sign=False)} ({chg})', 
        color='blue')
    if leverage:
        ax[0].plot(df.index, df['net_value'], 
            label=f'NAV: {utils.fmt_value(df.iloc[-1]["net_value"], pos_sign=False)} ({chg})', 
            color='darkgreen')
        chg=utils.fmt_value(df.iloc[-1]["lev_value"]-df.iloc[0]["lev_value"])
        ax[0].plot(df.index, df['lev_value'], 
            label=f'Liability: {utils.fmt_value(df.iloc[-1]["lev_value"], pos_sign=False)} ({chg})', 
            color='darkred')

    tgt_val=utils.fmt_value(
        df.iloc[-1]["cash"]/df.iloc[-1]["total_value"],vtype="pct",pos_sign=False)
    ax[0].fill_between(
        df.index, df['cash'], 0, 
        color='green', alpha=0.5, 
        label=f'Cash ({tgt_val}; {utils.fmt_value(df.iloc[-1]["cash"], pos_sign=False)})')
    df_accu=df['cash']
    for idx,tgt in enumerate(tgts):
        tgt_val=utils.fmt_value(
            df.iloc[-1][tgt+"_value"]/df.iloc[-1]["total_value"],vtype="pct",pos_sign=False)
        tgt_val=f'({tgt_val}; {utils.fmt_value(df.iloc[-1][f"{tgt}_value"], pos_sign=False)})'
        ax[0].fill_between(
            df.index, df[tgt+'_value']+df_accu, df_accu,
            color=port_colors[idx], alpha=0.5, linewidth=0.5,
            label=f'{tgt} {tgt_val}')
        df_accu=df_accu+df[tgt+'_value']
    #ax[0].set_yscale('log')
    
    basics_str='\n'.join([ f'{key}: {utils.fmt_value(att_dic[key])}' for key in att_dic])
    ax[0].text(0.3, 0.95, basics_str, transform=ax[0].transAxes, color='grey',
        bbox=dict(facecolor='white', alpha=0.5, edgecolor='lightgrey'),
        fontsize=const.TINY_SIZE, verticalalignment='top')
    
    ax[0].set_ylabel('Value')
    ax[0].legend(loc='upper left',fontsize=const.SM_SIZE)
    ax[0].set_title('Portfolio Performance valid from '+str(df.index[0].date())+' to '+str(df.index[-1].date())+f' ({total_days} days)')

    # ------------plot 1: return rate
    if df.iloc[-1]['accu_fund']>0:
        ax[1].plot(df.index, df['fund_change'], 
            label=f'Total Assets ARR ({utils.fmt_value(df.iloc[-1]["fund_change"],vtype="pct")})',
            color='blue', linewidth=1)
    if withbase:
        cagr_str=utils.fmt_value(mathlib.cagr(df.iloc[-1]['baseline_return']-1,total_days),vtype="pct")
        ax[1].plot(df.index, df['baseline_return']-1, 
                label=f'Baseline ({utils.fmt_value(df.iloc[-1]["baseline_return"]-1,vtype="pct")}|{cagr_str})',
                color='orange', linewidth=1)
    twr=df.iloc[-1]["accum_return"]-1
    cagr_str=utils.fmt_value(mathlib.cagr(twr,total_days),vtype="pct")
    ax[1].plot(df.index, df['accum_return']-1, 
               label=f'Total Assets TWR ({utils.fmt_value(twr,vtype="pct")}|{cagr_str})', 
               color='blue')
    if leverage:
        twr=df.iloc[-1]["accum_net_return"]-1
        cagr_str=utils.fmt_value(mathlib.cagr(twr,total_days),vtype="pct")
        ax[1].plot(df.index, df['accum_net_return']-1,
                   label=f'NAV TWR ({utils.fmt_value(twr,vtype="pct")}|{cagr_str})',
                   color='darkgreen') 
    no_risk=df['norisk_total_value']/df['accu_fund']
    if df.iloc[-1]['accu_fund']>0:
        ax[1].plot(df.index, no_risk-1, 
               label=f'Total Assets NoRisk ARR ({utils.fmt_value(no_risk[-1]-1,vtype="pct")})', 
               color='grey', linewidth=1.5)
    
    ax[1].axhline(y=0.0, linewidth=1, color='blue', linestyle='--')
    ax[1].tick_params(axis='y', labelcolor='blue')
    ax[1].set_ylabel('Accumulated Return', color='blue')
    ax[1].legend(loc='upper left',fontsize=const.SM_SIZE)

    # Create a twin axes on the right for the monthly bar chart
    ax_bar = ax[1].twinx()
    pct_dr=np.exp(df['daily_return'])
    # Resample the data to monthly and plot the bar chart on the right y-axis
    mon_return=pct_dr.resample('M').apply(lambda x: x.prod() - 1)
    
    width=20
    if leverage:
        width=width/2
        pct_dr_net=np.exp(df['daily_net_return'])
        mon_net_return=pct_dr_net.resample('M').apply(lambda x: x.prod() - 1)
        colors = ['darkgreen' if x > 0 else 'darkred' for x in mon_net_return]
        ax_bar.bar(
            mon_net_return.index- pd.offsets.MonthBegin(1) + pd.Timedelta(width*1.5, 'D'), mon_net_return, 
            width=width, color=colors, alpha=0.5, label='Monthly Net Return')
    colors = ['blue' if x > 0 else 'coral' for x in mon_return]
    ax_bar.bar(
        mon_return.index- pd.offsets.MonthBegin(1) + pd.Timedelta(width/2, 'D'), mon_return, 
        width=width, color=colors, alpha=0.3, label='Monthly Return')
    ax_bar.set_ylabel('Monthly Return', color='red')
    ax_bar.tick_params(axis='y', labelcolor='red')
    
    hlines=[(0.1,'green',0.5,'--'),(0.05,'green',0.5,':'),
            (0,'red',1,'--'),(-0.05,'red',0.5,':'),
            (-0.1,'red',0.5,'--')]
    for hline in hlines:
        ax_bar.axhline(
            y=hline[0], color=hline[1], linewidth=hline[2], linestyle=hline[3])
    '''
    if twr.max()>10: 
        ax[1].set_yscale('symlog')
        ticker=[-1.0, -0.75, -0.5, -0.25, -0.1, 0.0, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 30.0, 50.0]
        ax[1].yaxis.set_ticks(ticker)
        ax[1].set_yticklabels(ticker)
    else:
        ax[1].set_yscale('linear')
    '''
    # ------------plot 2: maximum drawdown
    if not financing: 
        
        # net value drawdown
        if leverage:
            max_str=utils.fmt_value(-df["net_drawdown"].max(),vtype="pct")
            latest_str=utils.fmt_value(-df["net_drawdown"].iloc[-1],vtype="pct")
            ax[2].plot(df.index, -df['net_drawdown'], alpha=0.5, 
                    label=f'NAV_Drawdown (Max: {max_str}|Latest: {latest_str})', color='darkred')
            ax[2].fill_between(
                df.index, -df['net_drawdown'], 0, where=df['net_drawdown']>0, color='lightcoral',alpha=0.5)
    
        if withbase:    
            ax[2].plot(df.index, -df['baseline_drawdown'], color='orange', alpha=0.5, 
                label=f'Baseline (Max: {utils.fmt_value(-df["baseline_drawdown"].max(),vtype="pct")})')
            ax[2].fill_between(
                df.index, -df['baseline_drawdown'], 0, where=df['baseline_drawdown']>0, color='yellow', alpha=0.3)
        
        # total assets drawdown
        max_str=utils.fmt_value(-df["drawdown"].max(),vtype="pct")
        latest_str=utils.fmt_value(-df["drawdown"].iloc[-1],vtype="pct")
        ax[2].plot(df.index, -df['drawdown'], alpha=0.3, 
                label=f'Drawdown (Max: {max_str}|Latest: {latest_str})', color='blue')
        ax[2].fill_between(
            df.index, -df['drawdown'], 0, where=df['drawdown']>0, color='dodgerblue',alpha=0.5)
        
        
        hlines=[(0.0,'black',1,'-'),(-0.05,'green',0.5,':'),(-0.1,'green',0.5,':'),
                (-0.15,'green',0.5,'--'),(-0.2,'orange',0.5,'--'),
                (-0.25,'orange',1,'--'),(-0.3,'red',1,'--')]
        if withbase:
            for hline in hlines:
                if abs(hline[0])<df['baseline_drawdown'].max():
                    ax[2].axhline(y=hline[0], color=hline[1], linewidth=hline[2], 
                                linestyle=hline[3])
        
        if leverage:
            entry='net_drawdown'
        else:
            entry='drawdown'
        df.loc[:,'drawperiod'] = df[entry].values > 0
        # calculate periods when all values are larger than 0
        df.loc[:, 'group'] = (df['drawperiod'] != df['drawperiod'].shift()).cumsum()
        df.loc[:, 'period'] = df.groupby('group')['drawperiod'].transform('cumsum')
        df.loc[:, 'period'] = df['period'].diff(periods=-1)
        
            
        longest_periods = df.sort_values('period', ascending=False).head(5)['group'].unique()
        df.loc[:, 'period_mark'] = df['group'].apply(
            lambda x: df.loc[df['group'] == x, 'period'].iloc[0] if x in longest_periods else 0)
        
        # 5 major drawdown periods
        for period in longest_periods:
            start_date = df.loc[df['group'] == period].index[0]
            end_date = df.loc[df['group'] == period].index[-1]
            max_lv=df[entry].loc[start_date:end_date].max()
            if max_lv<0.05:
                continue
            ax[2].axvspan(start_date, end_date, alpha=0.3, color='lightgrey')
            x,y=start_date,-max_lv
            ax[2].text(x, y/2, 
                f'{utils.fmt_value(y,vtype="pct")}\n({(end_date-start_date).days}days)', 
                ha='left', va='bottom', fontsize=const.SM_SIZE,
                weight='bold')
        # the last drawdown period, if any
        if df['drawperiod'].iloc[-1]>0:
            idx=-1
            while (df['drawperiod'].iloc[idx]>0)and (abs(idx)<len(df)):
                idx-=1
            start_date = df.index[idx]
            end_date = df.index[-1]
            max_lv=df[entry].loc[start_date:end_date].max()
            ax[2].axvspan(start_date, end_date, alpha=0.4, color='coral')
            x,y=start_date,-max_lv
            ax[2].text(x, -0.05, 
                f'{utils.fmt_value(y,vtype="pct")}\n({(end_date-start_date).days}days)', 
                ha='left', va='bottom', fontsize=const.SM_SIZE,
                weight='bold')
    
        #if leverage:
        ax_lev = ax[2].twinx()
        lev_r=100*df['lev_ratio']
        ax_lev.plot(
            df.index, lev_r, label=f'Leveraged Ratio', color='red',
            linewidth=1, alpha=0.5)
        ax_lev.set_ylabel('Leveraged Ratio', color='red')
        ax_bar.tick_params(axis='y', labelcolor='red')
        ax[2].legend(loc='lower left',fontsize=const.SM_SIZE)
        ax[2].set_ylabel('Drawdown')
    
    else:
        # ------------plot 2: funding pulse
        fund_pulse=df['accu_fund'].diff()
        ax[2].plot(df.index, fund_pulse, color='red', linewidth=1,alpha=0.7)
        ax[2].set_ylabel('Cash Flow')
    
    
    # ------------plot 3: annual return
    # calculate cumulative sum of log daily return
    cumy_return = np.exp(df['daily_return'].groupby(df.index.year).cumsum())-1
    cumy_return.loc[(df.index.month == 1) & (df.index.day == 1)] = np.nan
    #cum_log_return = cum_log_return.groupby(cum_log_return.index.year).apply(lambda x: pd.Series(x).cumsum())
    #cum_log_return.index = cum_log_return.index.map(lambda x: pd.date_range(start=x.date(), periods=len(x), freq='D'))
    ax[3].plot(
        cumy_return.index, cumy_return, color='blue', linewidth=1, alpha=0.5)
    if leverage:
        cumy_return = np.exp(df['daily_net_return'].groupby(df.index.year).cumsum())-1
        cumy_return.loc[(df.index.month == 1) & (df.index.day == 1)] = np.nan
        #cum_log_return = cum_log_return.groupby(cum_log_return.index.year).apply(lambda x: pd.Series(x).cumsum())
        #cum_log_return.index = cum_log_return.index.map(lambda x: pd.date_range(start=x.date(), periods=len(x), freq='D'))
        ax[3].plot(
            cumy_return.index, cumy_return, color='darkgreen', linewidth=1, alpha=0.5)
    
    ax[3].set_ylabel('Annual Cumulative Return')

    ax_bar2=ax[3].twinx()
    # Resample the data to monthly and plot the bar chart on the right y-axis
    yr_return=pct_dr.resample('Y').apply(lambda x: x.prod() - 1)
    width=365
    if leverage: 
        width=width/2
        yr_net_return=pct_dr_net.resample('Y').apply(lambda x: x.prod() - 1)
        colors = ['darkgreen' if x > 0 else 'darkred' for x in yr_net_return]
        bars2=ax_bar2.bar(
            #yr_return.index- pd.offsets.YearBegin(1), yr_return, 
            yr_net_return.index- pd.offsets.YearBegin(1) + pd.Timedelta(width*1.5, 'D'), yr_net_return, 
            width=width, color=colors, alpha=0.5, label='Annual Net Return',
            edgecolor='black', linewidth=1)
        # add value on top of each bar
        for bar in bars2:
            x = bar.get_x() + bar.get_width() / 2
            y = bar.get_height()
            ax_bar2.text(x, y, utils.fmt_value(y,vtype="pct"), 
                ha='center', va='bottom', fontsize=const.SM_SIZE,
                weight='bold')
    colors = ['dodgerblue' if x > 0 else 'coral' for x in yr_return]
    bars=ax_bar2.bar(
        #yr_return.index- pd.offsets.YearBegin(1), yr_return, 
        yr_return.index- pd.offsets.YearBegin(1) + pd.Timedelta(width/2, 'D'), yr_return, 
        width=width, color=colors, alpha=0.5, label='Annual Return',
        edgecolor='black', linewidth=1)
    # add value on top of each bar
    for bar in bars:
        x = bar.get_x() + bar.get_width() / 2
        y = bar.get_height()
        ax_bar2.text(x, y, utils.fmt_value(y,vtype="pct"), 
            ha='center', va='bottom', fontsize=const.SM_SIZE,
            weight='bold')


    hlines=[(0.5,'green',0.5,'--'),(0.25,'green',0.5,':'),
            (0,'grey',1,'--'),(-0.1,'red',0.5,':'),
            (-0.2,'red',0.5,'--'),(-0.3,'red',1.0,'--')]
    for hline in hlines:
        ax_bar2.axhline(
            y=hline[0], color=hline[1], linewidth=hline[2], linestyle=hline[3])
    ax_bar2.set_ylim(ax[3].get_ylim()) 

    # Set the x-axis label and title
    plt.xlabel('Date')

    # Show the plot
    #plt.show()
    plt.savefig(fig_fn, bbox_inches='tight', dpi=const.DPI)
    os.system(f'magick +dither {fig_fn} {fig_fn}')
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
        
    #plt.show()
    cfg=oculus.cfg
    figname=cfg['POSTPROCESS']['figname']
    #figname=os.path.join('./fig/', oculus.model_name+'.'+oculus.ticker+'.png')
    plt.savefig(figname, bbox_inches='tight', dpi=const.DPI)

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

def draw_histograms(x, xnames, fig_fn):
    '''
    x (nsamples, nfeatures) is a numpy array
    '''
    fig, ax = plt.subplots(1, 1)
    for i, xname in enumerate(xnames):
        ax.hist(x[:,i], alpha=0.5, bins=50, label=xname)
    ax.legend() 
    print(np.percentile(x, [10, 25, 50, 75, 90, 95, 99]))
    #ax.set_yscale('log')
    plt.savefig(fig_fn, bbox_inches='tight', dpi=const.DPI)
def draw_corr_heatmap(cr_mtx, xnames, fig_fn): 
    sns.heatmap(cr_mtx, cmap='coolwarm', 
                annot=True, fmt='.1f', 
                xticklabels=xnames, yticklabels=xnames)
    plt.title('Correlation Heatmap')
    plt.xlabel('Tickers')
    plt.ylabel('Tickers')
    plt.savefig(fig_fn, bbox_inches='tight', dpi=const.DPI)

def get_info(y, ybase):
    info='Win: {:.1%} ({:.1%})\n'.format((y>0).sum()/len(y),(ybase>0).sum()/len(ybase))
    info=info+'Return: {:.2%} ({:.2%})'.format(y.mean(), ybase.mean())
    return info

def table_print(table, table_fmt='fancy_grid'):
    from tabulate import tabulate
    return tabulate(table,headers='keys',tablefmt=table_fmt)


def append_dic_table(dic, dic_new, column_name='Value', index_name='Index'):
    if dic=={}:
        dic['header']=[index_name, column_name]
        for k,v in dic_new.items():
            dic[k]=[v]
    else:
        dic['header'].append(column_name)
        for k,v in dic_new.items():
            dic[k].append(v)
    return dic

def dic2html_CN(table_data):
    
    # Create the HTML table
    table_html = '<table style="border-collapse: collapse; font-family: Arial, sans-serif; font-size: 14px;">'
    try: 
        column_names = table_data['header']
        # Add the table header row
        table_html += '<tr>'
        for column_name in column_names:
            table_html += f'<th style="font-weight: bold; padding: 8px;">{column_name}</th>'
        table_html += '</tr>'
        header = True
    except KeyError:
        # no header
        header=False
    
    # Get the list of column names from the dictionary keys
    # Add the table data rows
    for i, (k, v) in enumerate(table_data.items()):
        if header:
            header=False
            continue
        table_html += '<tr>'
        # Add alternating background colors to the table rows
        if i % 2 == 0:
            bg_color = '#f9f9f9'
        else:
            bg_color = '#ddd'
        table_html += f'<td style="font-weight: bold; background-color: {bg_color};padding: 8px;">{k}</td>'
        table_html += f'<td style="background-color: {bg_color};  padding: 8px;">{v}</td>'
        table_html += '</tr>'
    table_html += '</table>'
    return table_html

def dic2html(table_data):
    
    
    # Create the HTML table
    table_html = '<table style="border-collapse: collapse; font-family: Arial, sans-serif; font-size: 14px;">'
    try: 
        column_names = table_data['header']
        # Add the table header row
        table_html += '<tr>'
        for column_name in column_names:
            table_html += f'<th style="font-weight: bold; padding: 8px;">{column_name}</th>'
        table_html += '</tr>'
        header = True
    except KeyError:
        # no header
        header=False
    
    # Get the list of column names from the dictionary keys
    # Add the table data rows
    for i, (k, v) in enumerate(table_data.items()):
        if header:
            header=False
            continue
        table_html += '<tr>'
        # Add alternating background colors to the table rows
        if i % 2 == 0:
            bg_color = '#f9f9f9'
        else:
            bg_color = '#ddd'
        table_html += f'<td style="font-weight: bold; background-color: {bg_color};padding: 8px;">{k}</td>'
        for itm in v:
            table_html += f'<td style="background-color: {bg_color};  padding: 8px;">{itm}</td>'
        table_html += '</tr>'
    table_html += '</table>'
    return table_html

def fmt_dic(dic):
    for k,v in dic.items():
        fmt_str=''
        for kw in ['value','fund','cash', 'accu_fund']:
            if kw in k:
                fmt_str='usd'
        for kw in ['return','drawdown','change']:
            if kw in k:
                fmt_str='pct'
        dic[k]=utils.fmt_value(v,fmt_str, pos_sign=False)
    return dic