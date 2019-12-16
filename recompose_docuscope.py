# docuscope specific recompilation procedure. for use with docuscope tagged ata only

import os
import pandas as pd
# in_root = 'follmann_andrew_output/follmann_andrew-2019-11-05-082505/token_csv'
in_root = r'../docuscope tagged/follman_andrew_2_output/cleaned-2019-12-03-093252/token_csv'
out_root = '../docuscope tagged/recompose_20191208'


def recompose_from_csv(fp):
    df = pd.read_csv(fp,
                     header=None,
                     names=('word', 'token', 'sc', 'tag', 'ngram_index'),
                     keep_default_na=False)

    if df.shape[0] < 5:
        return
    df = df[df['ngram_index'] != '']
    df['ngram_index'] = df['ngram_index'].astype(float).astype(int)
    df['cumcount'] = df.groupby('ngram_index').cumcount()
    df.loc[df['ngram_index'] != 0, 'cumcount'] = pd.np.nan
    df['cumcount'] = df['cumcount'].ffill()
    df_gb = df.groupby('cumcount').agg({'token': lambda x: '_'.join(x.tolist()), 'tag': 'first'})
    df_gb['tagged_inplace'] = df_gb['token'] + '##' + df_gb['tag'].fillna('UNTAGGED')
    return ' '.join(df_gb['tagged_inplace'])


def recompose_directory(in_root, out_root):
    if not os.path.exists(out_root):
        os.makedirs(out_root)
    for f in os.listdir(os.path.join(in_root)):
        out_fp  =os.path.join(out_root,f.replace('.csv', '.txt'))
        # if os.path.exists(out_fp):
        #     continue
        print('workign on ', f)
        text = recompose_from_csv(os.path.join(in_root, f))
        if text == '':
            print('no text')
        if text is not None:
            with open(out_fp, 'w',encoding='utf_8') as tfile:
                tfile.write(text)


if __name__ == '__main__':
    recompose_directory(in_root, out_root)
