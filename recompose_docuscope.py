import os
import pandas as pd
in_root = 'follmann_andrew_output/follmann_andrew-2019-11-05-082505/token_csv'
out_root = 'CBE/tagged'


def recompose_from_csv(fp):
    df = pd.read_csv(fp,
                     header=None,
                     names=('word', 'token', 'sc', 'tag', 'ngram_index'),
                     keep_default_na=False)
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
        print('workign on ', f)
        text = recompose_from_csv(os.path.join(in_root, f))
        with open(os.path.join(out_root,f.replace('.csv', '.txt')), 'w',encoding='utf_8') as tfile:
            tfile.write(text)


if __name__ == '__main__':
    recompose_directory(in_root, out_root)
