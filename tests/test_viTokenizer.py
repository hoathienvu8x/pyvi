from unittest import TestCase
from pyvi.ViTokenizer import ViTokenizer

class TestViTokenizer(TestCase):
    def test_sylabelize(self):
        cases_ = [
            [
                "Thủ tướng: Chỉ số thị trường chứng khoán Việt Nam trong top 3 thế giới",
                ['Thủ', 'tướng', ':', 'Chỉ', 'số', 'thị', 'trường', 'chứng', 'khoán', 'Việt', 'Nam', 'trong',
                        'top', '3', 'thế', 'giới']
            ],
            [
                "FLC đề nghị hủy toàn bộ giao dịch cổ phiếu đột biến ngày 1/4 nếu phát hiện vi phạm",
                ["FLC", "đề", "nghị", "hủy", "toàn", "bộ", "giao", "dịch", "cổ", "phiếu", "đột", "biến",
                 "ngày", "1/4", "nếu", "phát", "hiện", "vi", "phạm"]
            ],
            [
                "Công ty Cổ phần Tập đoàn FLC (HoSE: FLC) vừa có văn bản gửi Bộ Tài chính, Uỷ ban Chứng" \
                "khoán Nhà nước, Sở Giao dịch chứng khoán TP. HCM và Trung tâm Lưu ký Chứng khoán Việt" \
                "Nam đề nghị kiểm tra giao dịch đột biến trong ngày đối với cổ phiếu FLC.",
                ['Công', 'ty', 'Cổ', 'phần', 'Tập', 'đoàn', 'FLC', '(', 'HoSE', ':', 'FLC', ')', 'vừa', 'có',
                 'văn', 'bản', 'gửi', 'Bộ', 'Tài', 'chính', ',', 'Uỷ', 'ban', 'Chứng', 'khoán', 'Nhà', 'nước',
                 ',', 'Sở', 'Giao', 'dịch', 'chứng', 'khoán', 'TP.', 'HCM', 'và', 'Trung', 'tâm', 'Lưu', 'ký',
                 'Chứng', 'khoán', 'Việt', 'Nam', 'đề', 'nghị', 'kiểm', 'tra', 'giao', 'dịch', 'đột', 'biến',
                 'trong', 'ngày', 'đối', 'với', 'cổ', 'phiếu', 'FLC', '.']
            ]
        ]
        for item in cases_:
            actual = ViTokenizer.sylabelize(item[0])
            expected = item[1]
            self.assertEqual(actual, expected)

    def test_sylabelize_2(self):
        texts = open("tokenize_sets.txt").readlines()
        n = int(len(texts) / 3)
        for i in range(n + 1):
            text = texts[i * 3].strip()
            expected = texts[i * 3 + 1].strip()
            actual_text = " ".join(ViTokenizer.sylabelize(text))
            self.assertEqual(actual_text, expected)

