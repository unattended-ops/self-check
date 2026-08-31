"""문자열 목록에서 중복을 제거하되 원래 순서를 유지하는 순수 함수."""

from typing import Iterable, List


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    """중복을 제거한 새 리스트를 반환한다.

    - 입력을 변형하지 않는다(순수 함수).
    - 처음 등장한 위치의 순서를 그대로 유지한다.
    - 문자열은 정확히 일치할 때만 중복으로 본다(대소문자·공백 구분).

    Args:
        items: 문자열들의 이터러블.

    Returns:
        중복이 제거된 새로운 리스트.

    Raises:
        TypeError: items가 이터러블이 아니거나 원소가 문자열이 아닐 때.
    """
    if isinstance(items, str) or not hasattr(items, "__iter__"):
        raise TypeError("items must be an iterable of str")

    seen = set()
    result: List[str] = []
    for item in items:
        if not isinstance(item, str):
            raise TypeError(f"element must be str, got {type(item).__name__}")
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _run_tests() -> None:
    # 기본 동작: 첫 등장 순서 유지
    assert dedupe_preserve_order(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]

    # 빈 입력
    assert dedupe_preserve_order([]) == []

    # 중복 없음: 그대로 유지
    assert dedupe_preserve_order(["x", "y", "z"]) == ["x", "y", "z"]

    # 전부 동일
    assert dedupe_preserve_order(["같은값"] * 5) == ["같은값"]

    # 대소문자 구분
    assert dedupe_preserve_order(["Apple", "apple", "APPLE"]) == [
        "Apple",
        "apple",
        "APPLE",
    ]

    # 공백·빈 문자열 구분
    assert dedupe_preserve_order(["", " ", "", " ", "a"]) == ["", " ", "a"]

    # 유니코드 및 긴 목록
    assert dedupe_preserve_order(["가", "나", "가", "다", "나"]) == ["가", "나", "다"]

    # 순수성: 원본 리스트가 변형되지 않는다
    src = ["p", "q", "p"]
    snapshot = list(src)
    out = dedupe_preserve_order(src)
    assert src == snapshot
    assert out is not src

    # 제너레이터 입력도 처리
    gen = (s for s in ["m", "n", "m", "o"])
    assert dedupe_preserve_order(gen) == ["m", "n", "o"]

    # 튜플 입력 -> 리스트 반환
    assert dedupe_preserve_order(("t1", "t2", "t1")) == ["t1", "t2"]

    # 동일 입력 반복 호출 시 항상 동일 결과(결정성)
    data = ["k1", "k2", "k1", "k3"]
    assert dedupe_preserve_order(data) == dedupe_preserve_order(data)

    # 문자열 자체를 넘기면 TypeError
    try:
        dedupe_preserve_order("abc")
    except TypeError:
        pass
    else:
        raise AssertionError("문자열 입력에 대해 TypeError가 발생해야 한다")

    # 비문자열 원소는 TypeError
    try:
        dedupe_preserve_order(["a", 1])
    except TypeError:
        pass
    else:
        raise AssertionError("비문자열 원소에 대해 TypeError가 발생해야 한다")

    # 이터러블이 아니면 TypeError
    try:
        dedupe_preserve_order(42)
    except TypeError:
        pass
    else:
        raise AssertionError("비이터러블 입력에 대해 TypeError가 발생해야 한다")

    print("all tests passed")


if __name__ == "__main__":
    _run_tests()
