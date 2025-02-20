import itertools
from mahjong.tile import TilesConverter
from mahjong.agari import Agari
import pandas as pd

import streamlit as st


NUM_SUUPAI = 9
N_PAIS_TENPAI = 13


def pai_list_to_str_1idx(pai_list):
    pai_list_1idx = list(map(lambda x: x + 1, pai_list))
    return "".join(map(str, pai_list_1idx))


class PaiList:
    _pai_list: list[int]

    def __init__(self, pai_list: list[int]):
        self._pai_list = pai_list
        self.validate()

    def validate(self) -> None:
        for x in self._pai_list:
            if x < 0 or 9 <= x:
                raise ValueError("牌の数字は1から9の範囲でなければなりません")
        cnt = [0 for i in range(NUM_SUUPAI)]  # 各牌の出現枚数
        for x in self._pai_list:
            cnt[x - 1] += 1
        for m in cnt:
            if m > 4:
                raise ValueError("5枚以上使われている牌があります")

    def __str__(self) -> str:
        pai_list_1idx = list(map(lambda x: x + 1, self._pai_list))
        return "".join(map(str, pai_list_1idx))

    def __len__(self) -> int:
        return len(self._pai_list)

    def to_34_array(self) -> list[int]:
        """Convert to list of pai ids which is in 0 to 33"""
        tiles_conv = TilesConverter()
        hand = tiles_conv.string_to_34_array(sou=str(self))
        return hand

    @classmethod
    def from_str(cls, s: str) -> "PaiList":
        for c in s:
            if not c.isdigit():
                raise ValueError("数字以外の入力が含まれています")
        pai_list = [int(c) - 1 for c in s]  # 1 idx to 0 idx
        return cls(pai_list)


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
    _pai_list: PaiList
    
    def __init__(self, pai_list: PaiList):
        self._pai_list = pai_list

    def calc_best_sutepai(self) -> pd.DataFrame:
        hand_len = len(self.pai_list)
        num_stepai = hand_len - N_PAIS_TENPAI
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
            assert len(hand_13) == N_PAIS_TENPAI
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

    @classmethod
    def from_str(cls, s: str) -> "TapaiHand":
        pai_list = PaiList.from_str(s)
        return cls(pai_list)


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
