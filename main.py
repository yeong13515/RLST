from rlst.core.koreapi import korea_api
from rlst.core.balance import balance
from rlst.core.stock_data_load import stock_data_loader
from rlst.strategy.find_boss import find_boss_stock

import pandas as pd

if __name__=="__main__":
    api = korea_api()
    find_boss = find_boss_stock()

    data_loader = stock_data_loader()
    #data_loader.load_index_data(".DJT", tick=True) 
    #data_loader.load_d_data('MAMA')
    #data_loader.load_m_data('MAMA', tick=True)


    codes = [
    'ASRT', 'SYNA', 'CRBP', 'STIM', 'CDW', 'EGAN', 'VFF', 'ADSE', 'PCH',
    'TCBX', 'EBIZ', 'RDI', 'STRL', 'XCUR', 'CNOB', 'CABA', 'WVE', 'CTKB',
    'CRBU', 'TARS', 'VTVT', 'REAX', 'ATEX', 'NTRB', 'ADAG', 'SBCF', 
    'JOUT', 'EPRX', 'NEXM', 'CSGP', 'BHF', 'CHCI', 'SNT', 'FTEL',
    'CLAR', 'BMRN', 'ASLE', 'BFC', 'WINT', 'CNET', 'VRA', 'BFC', 'WINT',
    'CUB', 'ZJYL', 'WERN', 'EBI', 'SOHU', 'NTRSO', 'BSCW', 'SRPT', 'XFOR',
    'CGNX', 'CRBU', 'EGAN', 'VIGI', 'RDI', 'MRAM', 'TCBI', 'RILY', 'ASNS',
    'CHCO', 'CRON', 'MLGO', 'CHSN', 'PT', 'ATRC', 'LPCN', 'USXF', 'LEGN',
    'USLM', 'TIGR', 'MTEK', 'SBC', 'NNE', 'KFFB', 'BHFAL', 'PUI', 'CUBWU',
    'CNET', 'BL', 'GCT', 'ACET', 'BHRB', 'KMB', 'GRIN', 'CTKB', 'WAVE',
    'CSBR', 'ACMR', 'CING', 'ADIL', 'JOUT', 'EPRX', 'STAA', 'FSLR', 'ACDC',
    'CSX', 'PDEX', 'VTHR', 'BGLC'
]

    # for code in codes:
    #     data_loader.load_d_data(f'{code}')

    total_list = []
    for code in codes:
        temp = find_boss.preprocessing(code, pd.read_csv(f"data/raw/d_csv/{code}_data.csv"))
        if temp != None:
            total_list.append(temp)

    total_df = pd.DataFrame(total_list)
    print(total_df)
    find_boss.scale_optics(codes, total_df)

    # test.current_price('AAPL')
    # test.fundamental('AAPL')


    # model_a = balance(name='model_a', initial_cash=1000)
    
    # model_a.buy('AAPL',3,230)
    
    # print(model_a.total_value())
    # print(model_a.unreal_pnl())
    # model_a.sell('AAPL',3,200)



    
