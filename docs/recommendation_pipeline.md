# Quy trinh AI Recommendation

## Thu thap du lieu

Du an su dung Amazon Video Games reviews va metadata. Review cung cap `user_id`, `item_id`, `rating`, `timestamp`; metadata cung cap title, category, price, image va average rating.

## Quan sat du lieu

Notebook thong ke users, items, interactions, sparsity, phan phoi rating, do dai sequence, top categories va top products. Cac bieu do duoc luu trong `ml/reports/figures/` neu can dua vao bao cao.

## Tien xu ly

- Loc du lieu bang k-core de giu user/item co du so tuong tac.
- Encode user/item thanh id so.
- Sap xep interaction theo timestamp.
- Tao sequence theo tung user.
- Chia leave-one-out: train la lich su, validation la item ke cuoi, test la item cuoi.

## Huan luyen va danh gia

- Baseline: Item-KNN.
- Mo hinh chinh: LSTM va GRU4Rec.
- Metric: HR@5, HR@10, HR@20, NDCG@5, NDCG@10, NDCG@20.
- Evaluation protocol: 1 positive item + 99 negative items.
- Checkpoint tot nhat duoc chon theo validation NDCG@10.

## Demo

Backend nap `GRU4Rec_best.pt` va `model_artifacts.pkl`. User moi duoc goi y san pham pho bien; user co lich su duoc goi y theo chuoi hanh vi xem, them gio hang, mua, thich hoac rating cao.

