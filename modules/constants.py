from pydantic import BaseModel

def question_sheet(pid: str) -> str:
    if pid.startswith("candy"):
        return "candy"
    return pid[0]


def is_easy(pid):
    return pid[0] in "ABCDEGHL" or pid in ("Z01", "Z02", "Z03")


def is_hard(pid):
    return pid[0] in "FIJKMN" or pid in ("Z04", "Z05", "Z06")
type_table = {'A': '變數/輸入輸出', 'B': '條件判斷/迴圈', 'C': '陣列/字串', 'D': '函式/遞迴', 'E': '結構',
              'G': '資料結構', 'L': '實作與除錯技巧', 'H': '運算思維實作實務解析 (基礎)', 'F': '時間複雜度', 'I': '枚舉/二分搜',
              'J': '貪心', 'K': '圖論', 'M': '動態規劃', 'N': '運算思維實作實務解析 (進階)', 'Z': '運算思維實作挑戰賽', "candy": "趣味賽"}
def create_f(k):
    return lambda pid:question_sheet(pid)==k
question_sheets = [("基礎班", is_easy), ("進階班", is_hard)]
for k, v in type_table.items():
    question_sheets.append((v, create_f(k)))
allows = {
    "26winter": {
        "contest_id": "37",
        "category": question_sheets
    }
}
class ContestRes(BaseModel):
    problems: list[str]
    categories: list[str]
    ranking: dict[str, dict[str, int]]
    max_score: dict[str, int]