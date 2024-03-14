###backtest save
import mplfinance as mpf
import pandas as pd
import os
import matplotlib.pyplot as plt


import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt

def backtest_save(stock, d, day_data, tm_stamp, slprice, entry_price, levels, color, foldertype, target):
    # print("------------------------------------------------------------------------")
    title_color = "green" if(foldertype == "bull") else "red"
    final_levels = []
    final_colors = []
    final_widths = []
    final_styles = []
    for level in levels:
        final_levels.append(level)
        final_colors.append(color)
        final_widths.append(1.0)
        final_styles.append("solid")

    final_levels.append(slprice)
    final_colors.append("white")
    final_widths.append(1.0)
    final_styles.append("solid")
    

    final_levels.append(entry_price)
    final_colors.append("yellow")
    final_widths.append(1.0)
    final_styles.append('dashdot')

    final_levels.append(target)
    final_colors.append("yellow")
    final_widths.append(5.0)
    final_styles.append('solid')

    day_data['Date'] = pd.to_datetime(day_data['timestamp'])
    day_data.set_index('Date', inplace=True)
    ap = mpf.make_addplot(day_data['VWAP'], color='white', secondary_y=False, linewidths=0.1)
    ap2 = mpf.make_addplot(day_data['volume'], panel=1)
    fg,ax = mpf.plot(day_data, type='candle', style='mike', hlines={"hlines":final_levels, "colors":final_colors, "linestyle":final_styles, "linewidths":final_widths},figratio=(20,20), returnfig=True, addplot=[ap,ap2],volume = True, title=foldertype + " : " + stock + "  " + tm_stamp[11:16], figscale=1.5)
    
    ax[0].grid(False)
    tup = d.timetuple()
    name_file = str(tup[2]) + " " + d.strftime("%b")

    try:
        folder_name = "{}-{}-{}".format(d.day, d.month, d.year)
        filename = "dates/{}/{}/{}.png".format(folder_name ,foldertype, tm_stamp[11:13] + "-" + tm_stamp[14:16] +"-" +  stock)
        os.makedirs("dates/{}/{}".format(folder_name, foldertype), exist_ok = True)
        plt.savefig(filename)
        plt.close()
        return filename
        
    except OSError as error:
        print("Directory '%s' can not be created")
    
    
    plt.close()

    # if(datetime.today().day == tup[2] and datetime.today().month == tup[1]):
    # folder_date = "/backtestimages/{}_{}_{}".format(d.day, d.month, d.year)
    # try:
    #     os.makedirs(folder_date, exist_ok = True)
    #     plt.savefig("{}/{}_{}.png".format(folder_date,tm_stamp[11:16], stock + " " + name_file))
    # except OSError as error:
    #     print("Directory '%s' can not be created")
    return None
