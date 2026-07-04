#!/usr/bin/env python3
"""
Workflow Lookup — 工作流检索系统
==================================
从 catalog.json 读取结构化目录, 根据用户输入匹配最佳工作流。

用法:
    python lookup.py --query "发文"         # 精确查找
    python lookup.py --query "我要发一篇文章" # 模糊匹配
    python lookup.py --list                 # 分类树
    python lookup.py --detail W01           # 工作流详情
    python lookup.py --category 内容生产     # 按分类浏览
    python lookup.py --validate             # 检查触发词冲突
    python lookup.py --interactive          # 交互模式
"""
import json
import os
import re
import sys
from pathlib import Path

CATALOG_PATH = Path(__file__).parent / "catalog.json"


def load_catalog() -> dict:
    if not CATALOG_PATH.exists():
        print(f"❌ catalog.json 未找到: {CATALOG_PATH}")
        sys.exit(1)
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_trigger_index(catalog: dict) -> dict:
    """
    构建反向索引: 每个触发词 → 工作流ID列表
    同时检测冲突: 同一个触发词出现在多个工作流中
    """
    trigger_map = {}
    conflicts = []
    for wid, wf in catalog["workflows"].items():
        for t in wf.get("triggers", []):
            t_norm = t.strip().lower()
            if t_norm in trigger_map:
                conflicts.append((t, trigger_map[t_norm], wid))
            else:
                trigger_map[t_norm] = wid
        # 同义词也加入索引
        for syn, target in (wf.get("synonyms") or {}).items():
            syn_norm = syn.strip().lower()
            if syn_norm in trigger_map and trigger_map[syn_norm] != wid:
                conflicts.append((syn, trigger_map[syn_norm], wid))
            else:
                trigger_map[syn_norm] = wid
    return trigger_map, conflicts


def match_workflow(query: str, catalog: dict, trigger_map: dict) -> list:
    """
    匹配算法:
    1. 精确匹配: 查询串完全等于触发词 → 得分 1.0
    2. 子串匹配: 触发词是查询的子串 → 得分 0.9 * len(触发词)/len(查询)
    3. 同义词匹配: 查询中的词匹配同义词 → 得分 0.7
    4. 排除词: 命中 exclude_triggers → -0.3
    """
    q = query.strip().lower()
    if not q:
        return []

    scores = {}  # wid → score
    reasons = {}  # wid → [匹配原因]

    for wid, wf in catalog["workflows"].items():
        score = 0.0
        reasons[wid] = []

        triggers = [t.lower() for t in wf.get("triggers", [])]
        excludes = [e.lower() for e in wf.get("exclude_triggers", [])]
        synonyms = {k.lower(): v.lower() for k, v in (wf.get("synonyms") or {}).items()}

        # 1. 精确匹配
        if q in triggers or any(t == q for t in triggers):
            score = 1.0
            reasons[wid].append(f"精确匹配触发词: {q}")
        else:
            # 2. 子串匹配 (触发词是查询的一部分)
            trigger_matches = [t for t in triggers if t in q]
            if trigger_matches:
                best_t = max(trigger_matches, key=len)
                len_ratio = max(len(best_t) / max(len(q), 1), 0.3)
                score = max(score, 0.9 * min(len_ratio, 1.0))
                reasons[wid].append(f"子串匹配: '{best_t}' 在 '{q}' 中 (得分 {score:.2f})")

            # 3. 同义词匹配
            syn_matches = [s for s in synonyms if s in q]
            if syn_matches:
                best_s = max(syn_matches, key=len)
                syn_score = 0.7
                score = max(score, syn_score)
                reasons[wid].append(f"同义词匹配: '{best_s}' → '{synonyms[best_s]}'")

            # 4. 如果只有单个词匹配, 提分
            q_tokens = re.findall(r'[\w一-鿿]+', q)
            matched_triggers = [t for t in triggers if any(tok in t or t in tok for tok in q_tokens)]
            if matched_triggers and score == 0:
                score = 0.4
                reasons[wid].append(f"部分匹配: {matched_triggers[:2]}")

        # 5. 排除词惩罚
        excl_matches = [e for e in excludes if e in q]
        for _ in excl_matches:
            score -= 0.3
            reasons[wid].append(f"排除命中: {excl_matches} (-0.3)")

        # 6. 状态惩罚 (draft状态降权)
        if wf.get("status") == "draft":
            score *= 0.6
            reasons[wid].append("状态=draft (降权 0.6)")

        if score > 0:
            scores[wid] = max(0.0, score)

    # 排序: 得分从高到低, 同分按优先级
    def sort_key(item):
        wid, score = item
        pri = catalog["workflows"][wid].get("priority", "P9")
        pri_order = {"P0": 0, "P1": 1, "P2": 2}
        return (-score, pri_order.get(pri, 9))

    sorted_wf = sorted(scores.items(), key=sort_key)

    return [{"wid": wid, "score": sc, "reasons": reasons.get(wid, [])}
            for wid, sc in sorted_wf]


# ── 输出格式化 ──

def format_workflow_short(wf: dict, wid: str) -> str:
    pri = wf.get("priority", "P?")
    status_icon = "✅" if wf.get("status") == "active" else "🔧"
    return f"  {status_icon} {wid}: {wf['name_zh']} ({wf['name']}) [P{pri}]"


def format_workflow_detail(wf: dict, wid: str) -> str:
    lines = []
    lines.append(f"╔══ {wid}: {wf['name_zh']} ═══")
    lines.append(f"║  英文名: {wf['name']}")
    lines.append(f"║  状态: {wf.get('status', '?')}")
    lines.append(f"║  优先级: {wf.get('priority', '?')}")
    lines.append(f"║  分类: {wf.get('category', '?')} > {wf.get('subcategory', '?')}")
    lines.append(f"║  触发词: {', '.join(wf.get('triggers', []))}")
    if wf.get("exclude_triggers"):
        lines.append(f"║  排除词: {', '.join(wf['exclude_triggers'])}")
    if wf.get("entry_script"):
        lines.append(f"║  脚本: {wf['entry_script']}")
    if wf.get("skill"):
        lines.append(f"║  技能: {wf['skill']}")
    lines.append(f"║  步骤 ({wf.get('steps_count', '?')}步):")
    for i, s in enumerate(wf.get("steps", [])):
        lines.append(f"║    {s}")
    if wf.get("prompts_file"):
        lines.append(f"║  Prompts: {wf['prompts_file']}")
    if wf.get("arch_doc"):
        lines.append(f"║  架构: {wf['arch_doc']}")
    lines.append(f"║  产出: {wf.get('output', '?')}")
    if wf.get("requires_manual"):
        lines.append(f"║  人工: {wf['requires_manual']}")
    if wf.get("notes"):
        lines.append(f"║  备注: {wf['notes']}")
    lines.append(f"╚══")
    return "\n".join(lines)


def show_category_tree(catalog: dict):
    print("\n📂 工作流分类总览\n")
    for cat in catalog["categories"]:
        print(f"\n{cat.get('icon', '📁')} {cat['name']} — {cat.get('description', '')}")
        print(f"   {'─' * 40}")
        for sub in cat.get("subcategories", []):
            wf_ids = sub.get("workflows", [])
            wf_names = []
            for wid in wf_ids:
                wf = catalog["workflows"].get(wid)
                if wf:
                    wf_names.append(f"{wid}:{wf['name_zh']}")
            print(f"   ├ {sub['name']}: {', '.join(wf_names)}")
    print()


def show_validation(catalog: dict):
    """检查触发词冲突和各类一致性问题"""
    trigger_map, conflicts = build_trigger_index(catalog)

    print("\n🔍 工作流目录验证\n")

    if conflicts:
        print("❌ 触发词冲突:\n")
        for word, w1, w2 in conflicts:
            print(f"   ⚡ '{word}' 同时属于 {w1} 和 {w2}")
            c1_name = catalog["workflows"].get(w1, {}).get("name_zh", w1)
            c2_name = catalog["workflows"].get(w2, {}).get("name_zh", w2)
            print(f"      → {w1} ({c1_name}) 与 {w2} ({c2_name}) 冲突")
        print()
    else:
        print("✅ 无触发词冲突\n")

    # 检查状态一致性
    print("📊 工作流状态:")
    for wid, wf in sorted(catalog["workflows"].items()):
        icon = "✅" if wf.get("status") == "active" else "🔧" if wf.get("status") == "draft" else "❌"
        print(f"   {icon} {wid}: {wf['name_zh']} ({wf.get('status', '?')})  P{wf.get('priority', '?')}")
    print()

    # 统计
    total = len(catalog["workflows"])
    active = sum(1 for w in catalog["workflows"].values() if w.get("status") == "active")
    draft = sum(1 for w in catalog["workflows"].values() if w.get("status") == "draft")
    print(f"总计: {total} | ✅ 活跃: {active} | 🔧 开发中: {draft}")
    print()


# ── 主入口 ──

def main():
    import argparse

    parser = argparse.ArgumentParser(description="工作流检索系统")
    parser.add_argument("--query", "-q", help="用户输入文本")
    parser.add_argument("--detail", "-d", help="查看工作流详情 (W01)")
    parser.add_argument("--list", "-l", action="store_true", help="显示分类树")
    parser.add_argument("--category", "-c", help="按分类浏览")
    parser.add_argument("--validate", "-v", action="store_true", help="检查触发词冲突")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    parser.add_argument("--fuzzy", "-f", action="store_true", help="启用更宽松的模糊匹配")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    args = parser.parse_args()

    catalog = load_catalog()
    trigger_map, _ = build_trigger_index(catalog)

    # ── 冲突检测 ──
    if args.validate:
        show_validation(catalog)
        return

    # ── 分类树 ──
    if args.list:
        show_category_tree(catalog)
        return

    # ── 按分类浏览 ──
    if args.category:
        cat_name = args.category
        found = False
        for cat in catalog["categories"]:
            if cat_name in (cat["id"], cat["name"]):
                found = True
                print(f"\n{cat.get('icon', '')} {cat['name']}: {cat.get('description', '')}\n")
                for sub in cat.get("subcategories", []):
                    print(f"  ├ {sub['name']}")
                    for wid in sub.get("workflows", []):
                        wf = catalog["workflows"].get(wid)
                        if wf:
                            print(f"  │  {format_workflow_short(wf, wid)}")
                print()
        if not found:
            print(f"未找到分类: {cat_name}")
        return

    # ── 工作流详情 ──
    if args.detail:
        wid = args.detail.upper()
        wf = catalog["workflows"].get(wid)
        if wf:
            print(format_workflow_detail(wf, wid))
        else:
            print(f"未找到工作流: {wid}")
        return

    # ── 查询匹配 ──
    if args.query:
        results = match_workflow(args.query, catalog, trigger_map)
        if not results:
            print("❌ 无匹配工作流\n")
            # 给建议
            print("💡 试试这些触发词:")
            all_triggers = []
            for wf in catalog["workflows"].values():
                all_triggers.extend(wf.get("triggers", []))
            for t in all_triggers[:10]:
                print(f"   · {t}")
            return

        if args.json:
            print(json.dumps(results[:5], ensure_ascii=False, indent=2))
            return

        print(f"\n🔎 查询: \"{args.query}\"\n")
        print(f"找到 {len(results)} 个匹配:\n")

        for i, r in enumerate(results[:5]):
            wf = catalog["workflows"][r["wid"]]
            icon = "✅" if wf.get("status") == "active" else "🔧"
            badge = "★" if i == 0 else " "
            print(f"  {badge} {r['wid']} ({r['score']:.2f}) {wf['name_zh']} {icon}")
            print(f"      {', '.join(wf.get('triggers', [])[:3])}...")
            if r.get("reasons"):
                print(f"      原因: {'; '.join(r['reasons'][:2])}")
            print()

        if results[0]["score"] == 0:
            print("⚠️  匹配度较低, 请核实触发词\n")
        elif results[0]["score"] >= 0.8:
            print(f"→ 推荐: {catalog['workflows'][results[0]['wid']]['name_zh']} (置信度 {results[0]['score']:.0%})")

        return

    # ── 交互模式 ──
    if args.interactive:
        print("\n🔍 Workflow Lookup 交互模式 (输入 q 退出)\n")
        while True:
            try:
                q = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not q or q.lower() == "q":
                break
            results = match_workflow(q, catalog, trigger_map)
            if not results:
                print("  ❌ 无匹配")
                continue
            for r in results[:3]:
                wf = catalog["workflows"][r["wid"]]
                print(f"  {r['wid']} ({r['score']:.2f}) {wf['name_zh']} — {', '.join(wf.get('triggers', [])[:3])}...")
            if results[0]["score"] >= 0.6:
                print(f"  → {catalog['workflows'][results[0]['wid']]['name_zh']}")
            print()
        return

    # ── 无参数 → 显示帮助 ──
    parser.print_help()
    print()
    show_category_tree(catalog)
    show_validation(catalog)


if __name__ == "__main__":
    main()
