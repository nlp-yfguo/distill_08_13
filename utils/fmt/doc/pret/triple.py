#encoding: utf-8

from math import ceil

from utils.fmt.base import get_bsize, pad_batch
from utils.fmt.doc.base import doc_reader as file_reader
from utils.fmt.doc.mono.base import map_batch as map_batch_pret
from utils.fmt.vocab.base import map_batch as map_batch_base

from cnfg.vocab.base import pad_id

map_batch = (map_batch_base, map_batch_pret,)

def batch_loader(finput, fpret, ftarget, bsize, maxpad, maxpart, maxtoken, minbsize, get_bsize=get_bsize, file_reader=file_reader, **kwargs):

	_f_maxpart = float(maxpart)
	rsi = []
	rsp = []
	rst = []
	nd = maxlen = minlen = mlen_i = mlen_p = mlen_t = nsent = 0
	for (i_d, i_lgth), (pd, p_lgth), (td, t_lgth) in zip(file_reader(finput), file_reader(fpret), file_reader(ftarget)):
		cur_nsent = len(i_d)
		lgth = i_lgth + p_lgth + t_lgth
		if maxlen == 0:
			_maxpad = max(1, min(maxpad, ceil(lgth / _f_maxpart)) // 2)
			maxlen = lgth + _maxpad
			minlen = lgth - _maxpad
			_bsize = max(1, get_bsize(lgth + _maxpad * 3, maxtoken, bsize) // cur_nsent)
			nsent = cur_nsent
		if (cur_nsent == nsent) and ((nd < minbsize) or (lgth <= maxlen and lgth >= minlen and nd < _bsize)):
			rsi.append(i_d)
			rsp.append(pd)
			rst.append(td)
			if i_lgth > mlen_i:
				mlen_i = i_lgth
			if p_lgth > mlen_p:
				mlen_p = p_lgth
			if t_lgth > mlen_t:
				mlen_t = t_lgth
			nd += 1
		else:
			yield rsi, rsp, rst, mlen_i, mlen_p, mlen_t, nsent
			rsi = [i_d]
			rsp = [pd]
			rst = [td]
			mlen_i = i_lgth
			mlen_p = p_lgth
			mlen_t = t_lgth
			nsent = cur_nsent
			_maxpad = max(1, min(maxpad, ceil(lgth / _f_maxpart)) // 2)
			maxlen = lgth + _maxpad
			minlen = lgth - _maxpad
			_bsize = max(1, get_bsize(lgth + _maxpad * 3, maxtoken, bsize) // cur_nsent)
			nd = 1
	if rsi:
		yield rsi, rsp, rst, mlen_i, mlen_p, mlen_t, nsent

def batch_mapper(finput, fpret, ftarget, vocabi, vocabp, vocabt, bsize, maxpad, maxpart, maxtoken, minbsize, map_batch=map_batch, batch_loader=batch_loader, **kwargs):

	_map_batch_base, _map_batch_pret = map_batch
	for i_d, pd, td, mlen_i, mlen_p, mlen_t, nsent in batch_loader(finput, fpret, ftarget, bsize, maxpad, maxpart, maxtoken, minbsize, **kwargs):
		rsi, extok_i = _map_batch_base(i_d, vocabi)
		rsp, extok_p = _map_batch_pret(pd, vocabp)
		rst, extok_t = _map_batch_base(td, vocabt)
		yield rsi, rsp, rst, mlen_i + extok_i, mlen_p + extok_p, mlen_t + extok_t, nsent

def batch_padder(finput, fpret, ftarget, vocabi, vocabp, vocabt, bsize, maxpad, maxpart, maxtoken, minbsize, pad_batch=pad_batch, batch_mapper=batch_mapper, pad_id=pad_id, **kwargs):

	for i_d, pd, td, mlen_i, mlen_p, mlen_t, nsent in batch_mapper(finput, fpret, ftarget, vocabi, vocabp, vocabt, bsize, maxpad, maxpart, maxtoken, minbsize, **kwargs):
		yield pad_batch(i_d, mlen_i, pad_id=pad_id), pad_batch(pd, mlen_p, pad_id=pad_id), pad_batch(td, mlen_t, pad_id=pad_id), nsent
