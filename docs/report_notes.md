# Ghi chu bao cao

## Ket qua hien co

| Model | HR@10 | NDCG@10 |
| --- | ---: | ---: |
| Item-KNN | 0.1378 | 0.1330 |
| LSTM | 0.4997 | 0.3031 |
| GRU4Rec | 0.5046 | 0.3059 |

Trong log validation, GRU4Rec dat moc tot nhat `HR@10=0.5484`, `NDCG@10=0.3370`. Khi bao cao, can ghi ro con so nao la validation best va con so nao la test/final.

## Tinh chinh tham so

Notebook goc co tinh chinh o muc co ban: `LR=1e-3`, `PATIENCE=7`, `weight_decay=1e-5`, scheduler giam learning rate va early stopping theo `NDCG@10`. Chua co grid search nhieu cau hinh.

## Truoc/sau tien xu ly

Notebook co so sanh thong ke truoc/sau k-core filtering ve interactions, users, items va phan phoi interaction. Chua train hai model rieng biet truoc/sau xu ly de so metric.

