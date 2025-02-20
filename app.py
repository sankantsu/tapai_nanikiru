import itertools
from mahjong.tile import TilesConverter
from mahjong.agari import Agari
import pandas as pd

import streamlit as st


NUM_SUUPAI = 9


def pai_list_to_str_1idx(pai_list):
    pai_list_1idx = list(map(lambda x: x + 1, pai_list))
    return "".join(map(str, pai_list_1idx))


class Hand13:
    pai_list: list[int]

    def __init__(self, pai_list) -> None:
        self.pai_list = pai_list

    def calc_machi(self) -> list[int]:
        machi = []
        tiles_conv = TilesConverter()
        agari_calc = Agari()
        for i in range(9):
            hand_14_pais = sorted(self.pai_list + [i])
            hand = tiles_conv.string_to_34_array(sou=pai_list_to_str_1idx(hand_14_pais))
            if agari_calc.is_agari(hand):
                machi.append(i)
        return machi


class TapaiHand:
    pai_list: list[int]
    
    def __init__(self, pai_list):
        self.pai_list = pai_list
        self.validate()

    def validate(self) -> None:
        for x in self.pai_list:
            if x < 0 or 9 <= x:
                raise ValueError("牌の数字は1から9の範囲でなければなりません")
        # 各牌の出現枚数
        cnt = [0 for i in range(NUM_SUUPAI)]
        for x in self.pai_list:
            cnt[x - 1] += 1
        for m in cnt:
            if m > 4:
                raise ValueError("5枚以上使われている牌があります")

    def calc_best_sutepai(self) -> pd.DataFrame:
        hand_len = len(self.pai_list)
        num_stepai = hand_len - 13
        results = []
        known_sutepai = set()
        for sutepai_idx in itertools.combinations(range(hand_len), num_stepai):
            hand_13 = []
            sutepai_list = []
            for i, pai in enumerate(self.pai_list):
                if i in sutepai_idx:
                    sutepai_list.append(pai)
                else:
                    hand_13.append(pai)
            assert len(hand_13) == 13
            sutepai_tuple = tuple(sutepai_list)
            if sutepai_tuple in known_sutepai:
                continue
            known_sutepai.add(sutepai_tuple)
            machi_list = Hand13(hand_13).calc_machi()
            if machi_list:
                results.append({
                    "捨て牌": pai_list_to_str_1idx(sutepai_list),
                    "13枚形": pai_list_to_str_1idx(hand_13),
                    "待ち": pai_list_to_str_1idx(machi_list),
                })
        df = pd.DataFrame.from_records(results)
        df = df.sort_values(
            by="待ち",
            key=lambda col: col.apply(lambda lst: len(lst)),
            ascending=False,
        )
        return df


def parse_hand(s: str) -> TapaiHand:
    for c in s:
        if not c.isdigit():
            raise ValueError("数字以外の入力が含まれています")
    pai_list = [int(c) - 1 for c in s]  # 1 idx to 0 idx
    return TapaiHand(pai_list)


def main():
    st.markdown("""
    # 多牌チンイツ何切る

    14 枚以上の任意の 1 色手の牌姿からどの牌を切ると広いテンパイがつくれるか計算します。

    ## 使用方法

    以下の入力欄に牌姿を入力してください (e.g. 123334566777889 (15 枚形))。
    捨て牌の候補, テンパイ形 および テンパイ時の待ちが表示されます。
    """)
    hand_str = st.text_input(label="牌姿 (14枚以上) を入力", placeholder="123334566777889")
    if hand_str:
        tapai_hand = parse_hand(hand_str)
        st.write(pai_list_to_str_1idx(tapai_hand.pai_list), f"{len(tapai_hand.pai_list)} 枚")

        results = tapai_hand.calc_best_sutepai()
        st.write(results)


if __name__ == "__main__":
    main()
