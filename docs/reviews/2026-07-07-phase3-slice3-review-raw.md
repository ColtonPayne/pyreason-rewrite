<!-- doccode: pyreason-rewrite-docs-reviews-phase3-slice3-review-raw -->
# Phase 3, slice 3 review — raw probe materials

The reviewer probes from [the review](2026-07-07-phase3-slice3-review.md),
verbatim, so the evidence is reproducible after the session scratchpad is
gone. Both scripts take no arguments; adjust the absolute `REPO` path if the
clone lives elsewhere.

Run commands (2026-07-07, both exercised as written):

```
# five-quirk verification, installed oracle only
oracle-env/bin/python quirks_oracle.py

# discriminating probes, both engines, diffed
PYTHONHASHSEED=0 oracle-env/bin/python probes.py 2>/dev/null | grep '^P|' > probes_a.txt
PYTHONHASHSEED=0 scripts/rewrite-python  probes.py 2>/dev/null | grep '^P|' > probes_b.txt
diff probes_a.txt probes_b.txt   # empty — 31/31 identical
```

Both engines' probe outputs were byte-identical:
`sha256(probes_a.txt) == sha256(probes_b.txt) ==
f4c1081c406f93060b07af00d8a0956a4211fc8ef086462727c18d521cc060e0`.

## quirks_oracle.py

```python
"""Empirical verification of the five claimed oracle quirks, installed oracle only."""
import networkx as nx
import pyreason as pr
from pyreason import Fact, Rule


def load(fact_end=2):
    g = nx.DiGraph()
    g.add_nodes_from(["John", "Mary", "Justin", "Dog", "Cat"])
    for e in [("Justin", "Mary"), ("John", "Mary"), ("John", "Justin")]:
        g.add_edge(*e, Friends=1)
    for e in [("Mary", "Cat"), ("Justin", "Cat"), ("Justin", "Dog"), ("John", "Dog")]:
        g.add_edge(*e, owns=1)
    pr.load_graph(g)
    pr.add_rule(Rule("popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)", "popular_rule"))
    pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, fact_end))


pr.settings.verbose = False
pr.settings.atom_trace = True

# Quirk 4: again=True with no program degrades to a fresh run
load()
interp = pr.reason(timesteps=2, again=True)
print("Q4 again-no-program get_time:", pr.get_time())

# Quirk 3: bare again with no new facts
try:
    pr.reason(timesteps=1, again=True)
    print("Q3 bare-again: NO RAISE")
except Exception as e:
    print(f"Q3 bare-again: {type(e).__module__}.{type(e).__qualname__}: {e}")

# Quirk 1: half-cleared program after reset()
prog_before = pr.get_logic_program()
pr.reset()
print("Q1 program is same object:", pr.get_logic_program() is prog_before)
print("Q1 program.interp:", pr.get_logic_program().interp)
print("Q1 get_interpretation():", pr.get_interpretation())
try:
    pr.get_time()
    print("Q1 get_time: NO RAISE")
except Exception as e:
    print(f"Q1 get_time: {type(e).__module__}.{type(e).__qualname__}: {e}")
# and the post-reset raise pair
try:
    pr.reason(timesteps=1)
    print("Q1 fresh-reason-after-reset: NO RAISE")
except Exception as e:
    print(f"Q1 fresh-reason-after-reset: {type(e).__qualname__}: {e}")
try:
    pr.reason(timesteps=1, again=True)
    print("Q1 again-reason-after-reset: NO RAISE")
except Exception as e:
    print(f"Q1 again-reason-after-reset: {type(e).__qualname__}: {e}")

# Quirk 5: grounding tables survive reset (module globals + observable IPL survival)
import pyreason.pyreason as prm
print("Q5 specific_graph_node_labels survived:",
      prm.__dict__.get('__specific_graph_node_labels') is not None)
print("Q5 clause_maps survived:", prm.__dict__.get('__clause_maps') is not None)
print("Q5 ipl-after-reset:", prm.__dict__.get('__ipl'))

# Quirk 2: restart=True resumes under an intact trace
load()
interp = pr.reason(timesteps=2)
pr.add_fact(Fact("popular(Justin)", "resume_fact", 0, 0))
interp2 = pr.reason(timesteps=2, again=True, restart=True)
print("Q2 get_time after restart-true:", pr.get_time())
try:
    interp2.get_dict()
    print("Q2 get_dict: NO RAISE")
except Exception as e:
    print(f"Q2 get_dict: {type(e).__qualname__}: {e.args!r}")
try:
    pr.filter_and_sort_nodes(interp2, ["popular"])
    print("Q2 filter_and_sort_nodes: NO RAISE")
except Exception as e:
    print(f"Q2 filter_and_sort_nodes: {type(e).__qualname__}: {e.args!r}")
```

## probes.py

```python
"""Discriminating lifecycle probes, run identically under both engines.

Every observation prints as one `P|<id>|<canonical json>` line; everything
else on stdout is engine noise to be filtered. Seams probed are exactly the
ones the committed 14 cases do not pin: cross-program state survival through
reset (IPL, name ledgers), reset_rules before any reason, reset_settings
after multiple non-default knobs, a second again-resume with no new facts
(the fact lists are NOT cleared by a resume), persistent get_dict over an
extended restart=False timeline, and two sequential full programs in one
process with and without reset.
"""
import sys
from pathlib import Path

REPO = Path("/Users/coltonpayne/Projects/pyreason-rewrite")
sys.path.insert(0, str(REPO))

from harness.compare import canonical_json  # stdlib-only module

import networkx as nx
import pyreason as pr
from pyreason import Fact, Rule


def emit(pid, value):
    print(f"P|{pid}|{canonical_json(value)}", flush=True)


def plain_df(df):
    return {"columns": [str(c) for c in df.columns],
            "rows": [list(r) for r in df.itertuples(index=False, name=None)]}


def frames(interp, labels):
    try:
        return [plain_df(f) for f in pr.filter_and_sort_nodes(interp, labels)]
    except Exception as e:
        return {"raised": True, "type": type(e).__qualname__, "args": [str(a) for a in e.args]}


def idict(interp):
    try:
        return interp.get_dict()
    except Exception as e:
        return {"raised": True, "type": type(e).__qualname__, "args": [str(a) for a in e.args]}


def outcome(fn):
    try:
        v = fn()
        return {"raised": False}, v
    except Exception as e:
        return {"raised": True, "type": f"{type(e).__module__}.{type(e).__qualname__}",
                "message": str(e)}, None


def popular_graph():
    g = nx.DiGraph()
    g.add_nodes_from(["John", "Mary", "Justin", "Dog", "Cat"])
    for e in [("Justin", "Mary"), ("John", "Mary"), ("John", "Justin")]:
        g.add_edge(*e, Friends=1)
    for e in [("Mary", "Cat"), ("Justin", "Cat"), ("Justin", "Dog"), ("John", "Dog")]:
        g.add_edge(*e, owns=1)
    return g


def node_heavy_graph():
    # More nodes than edges: the clause-reorder branch is NOT taken
    g = nx.DiGraph()
    g.add_nodes_from(["a", "b", "c", "d", "e", "f"])
    g.add_edge("a", "b", knows=1)
    g.add_edge("b", "c", knows=1)
    return g


POPULAR_RULE = "popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)"

pr.settings.verbose = False
pr.settings.atom_trace = True

# ---- P1: full program w/ IPL, reset, then a DIFFERENT program in-process ----
pr.load_graph(popular_graph())
pr.add_rule(Rule(POPULAR_RULE, "popular_rule"))
pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, 2))
pr.add_inconsistent_predicate("popular", "unpopular")
i1 = pr.reason(timesteps=2)
emit("p1-first-time", pr.get_time())
emit("p1-first-frames", frames(i1, ["popular"]))

pr.reset()
pr.load_graph(node_heavy_graph())
pr.add_rule(Rule("famous(x) <-1 famous(y), knows(x,y)", "famous_rule"))
pr.add_fact(Fact("famous(c)", "famous_fact", 0, 2))
i2 = pr.reason(timesteps=2)
emit("p1-second-time", pr.get_time())
emit("p1-second-frames", frames(i2, ["famous", "unpopular"]))
emit("p1-second-dict", idict(i2))
emit("p1-second-trace", plain_df(pr.get_rule_trace(i2)[0]))

# ---- P2: reset_rules BEFORE any reason, facts still loaded ----
pr.reset()
pr.load_graph(popular_graph())
pr.add_rule(Rule("wrong(x) <-1 wrong(y), Friends(x,y)", "wrong_rule"))
pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, 2))
pr.reset_rules()
emit("p2-rules-after", pr.get_rules() is None)
pr.add_rule(Rule(POPULAR_RULE, "popular_rule"))
i3 = pr.reason(timesteps=2)
emit("p2-time", pr.get_time())
emit("p2-frames", frames(i3, ["popular"]))

# ---- P3: reset_settings after several non-default knobs ----
pr.reset()
pr.settings.persistent = True
pr.settings.save_graph_attributes_to_trace = True
pr.settings.atom_trace = True
pr.reset_settings()
emit("p3-knobs-after-reset", [pr.settings.persistent, pr.settings.canonical,
                              pr.settings.atom_trace,
                              pr.settings.save_graph_attributes_to_trace,
                              pr.settings.verbose,
                              pr.settings.store_interpretation_changes])
pr.settings.verbose = False  # keep runs quiet in both engines
pr.load_graph(popular_graph())
pr.add_rule(Rule(POPULAR_RULE, "popular_rule"))
pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, 2))
i4 = pr.reason(timesteps=2)
emit("p3-trace-atomoff", plain_df(pr.get_rule_trace(i4)[0]))
emit("p3-dict-nonpersistent", idict(i4))

# ---- P4: again with new facts, then a SECOND again with none added ----
pr.reset()
pr.settings.atom_trace = True
pr.load_graph(popular_graph())
pr.add_rule(Rule(POPULAR_RULE, "popular_rule"))
pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, 2))
i5 = pr.reason(timesteps=2)
pr.add_fact(Fact("popular(Justin)", "resume_fact", 0, 0))
out, _ = outcome(lambda: pr.reason(timesteps=2, again=True, restart=False))
emit("p4-first-again-outcome", out)
emit("p4-first-again-time", pr.get_time())
# the resume did NOT clear the fact lists at the pin — a second bare again
# re-consumes the same resume fact instead of raising
out2, _ = outcome(lambda: pr.reason(timesteps=2, again=True, restart=False))
emit("p4-second-again-outcome", out2)
emit("p4-second-again-time", pr.get_time())
emit("p4-frames", frames(i5, ["popular"]))
emit("p4-dict", idict(i5))

# ---- P5: persistent get_dict over an extended restart=False timeline ----
pr.reset()
pr.settings.atom_trace = True
pr.settings.persistent = True
pr.load_graph(popular_graph())
pr.add_rule(Rule(POPULAR_RULE, "popular_rule"))
pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, 0))
i6 = pr.reason(timesteps=2)
pr.add_fact(Fact("special(Dog)", "special_fact", 0, 0, True))
out, _ = outcome(lambda: pr.reason(timesteps=2, again=True, restart=False))
emit("p5-again-outcome", out)
emit("p5-time", pr.get_time())
emit("p5-dict-persistent", idict(i6))

# ---- P6: two sequential full programs, NO reset between ----
pr.reset()
pr.reset_settings()
pr.settings.verbose = False
pr.settings.atom_trace = True
pr.load_graph(popular_graph())
pr.add_rule(Rule(POPULAR_RULE, "popular_rule"))
pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, 2))
i7 = pr.reason(timesteps=2)
emit("p6-first-time", pr.get_time())
pr.load_graph(node_heavy_graph())  # replace graph in place, rules survive
pr.add_fact(Fact("popular(a)", "second_fact", 0, 2))
out, _ = outcome(lambda: pr.reason(timesteps=2))
emit("p6-second-outcome", out)
emit("p6-second-time", pr.get_time())
i8 = pr.get_interpretation()
emit("p6-second-frames", frames(i8, ["popular"]))
emit("p6-second-dict", idict(i8))

# ---- P7: canonical/persistent alias through reset_settings + last write ----
pr.settings.canonical = True
pr.reset_settings()
emit("p7-alias-after-reset", [pr.settings.persistent, pr.settings.canonical])
pr.settings.persistent = True
pr.settings.canonical = False
emit("p7-last-write", [pr.settings.persistent, pr.settings.canonical])

# ---- P8: sequential fresh reason with no facts re-added ----
pr.reset()
pr.reset_settings()
pr.settings.verbose = False
pr.settings.atom_trace = True
pr.load_graph(popular_graph())
pr.add_rule(Rule(POPULAR_RULE, "popular_rule"))
pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, 2))
i9 = pr.reason(timesteps=2)
out, _ = outcome(lambda: pr.reason(timesteps=2))  # fresh program, no user facts
emit("p8-second-outcome", out)
emit("p8-second-time", pr.get_time())
i10 = pr.get_interpretation()
emit("p8-second-frames", frames(i10, ["popular"]))
```

## The 31 matched probe observations (identical under both engines)

```
P|p1-first-time|3
P|p1-first-frames|[{"columns":["component","popular"],"rows":[["Mary",[1,1]]]},{"columns":["component","popular"],"rows":[["Mary",[1,1]],["Justin",[1,1]]]},{"columns":["component","popular"],"rows":[["Mary",[1,1]],["John",[1,1]],["Justin",[1,1]]]}]
P|p1-second-time|3
P|p1-second-frames|[{"columns":["component","famous","unpopular"],"rows":[["c",[1,1],[0,1]]]},{"columns":["component","famous","unpopular"],"rows":[["c",[1,1],[0,1]],["b",[1,1],[0,1]]]},{"columns":["component","famous","unpopular"],"rows":[["c",[1,1],[0,1]],["b",[1,1],[0,1]],["a",[1,1],[0,1]]]}]
P|p1-second-dict|{"0":{"('a', 'b')":{},"('b', 'c')":{},"a":{},"b":{},"c":{"famous":[1,1]},"d":{},"e":{},"f":{}},"1":{"('a', 'b')":{},"('b', 'c')":{},"a":{},"b":{"famous":[1,1]},"c":{"famous":[1,1]},"d":{},"e":{},"f":{}},"2":{"('a', 'b')":{},"('b', 'c')":{},"a":{"famous":[1,1]},"b":{"famous":[1,1]},"c":{"famous":[1,1]},"d":{},"e":{},"f":{}}}
P|p1-second-trace|{"columns":["Time","Fixed-Point-Operation","Node","Label","Old Bound","New Bound","Occurred Due To","Consistent","Triggered By","Inconsistency Message","Clause-1","Clause-2"],"rows":[[0,0,"c","famous","[0.0,1.0]","[1.0,1.0]","famous_fact",true,"Fact","",null,null],[1,1,"c","famous","[0.0,1.0]","[1.0,1.0]","famous_fact",true,"Fact","",null,null],[1,1,"b","famous","[0.0,1.0]","[1.0,1.0]","famous_rule",true,"Rule","",["c"],[["b","c"]]],[2,2,"c","famous","[0.0,1.0]","[1.0,1.0]","famous_fact",true,"Fact","",null,null],[2,2,"b","famous","[0.0,1.0]","[1.0,1.0]","famous_rule",true,"Rule","",["c","b"],[["b","c"]]],[2,2,"a","famous","[0.0,1.0]","[1.0,1.0]","famous_rule",true,"Rule","",["c","b"],[["a","b"]]]]}
P|p2-rules-after|true
P|p2-time|3
P|p2-frames|[{"columns":["component","popular"],"rows":[["Mary",[1,1]]]},{"columns":["component","popular"],"rows":[["Mary",[1,1]],["Justin",[1,1]]]},{"columns":["component","popular"],"rows":[["Mary",[1,1]],["John",[1,1]],["Justin",[1,1]]]}]
P|p3-knobs-after-reset|[false,false,false,false,true,true]
P|p3-trace-atomoff|{"columns":["Time","Fixed-Point-Operation","Node","Label","Old Bound","New Bound","Occurred Due To","Consistent","Triggered By","Inconsistency Message"],"rows":[[0,0,"Mary","popular","-","[1.0,1.0]","-",true,"Fact",""],[0,0,"Mary","unpopular","-","[0.0,0.0]","IPL: popular",true,"IPL",""],[1,1,"Mary","popular","-","[1.0,1.0]","-",true,"Fact",""],[1,1,"Mary","unpopular","-","[0.0,0.0]","IPL: popular",true,"IPL",""],[1,1,"Justin","popular","-","[1.0,1.0]","-",true,"Rule",""],[1,1,"Justin","unpopular","-","[0.0,0.0]","IPL: popular",true,"IPL",""],[2,2,"Mary","popular","-","[1.0,1.0]","-",true,"Fact",""],[2,2,"Mary","unpopular","-","[0.0,0.0]","IPL: popular",true,"IPL",""],[2,2,"John","popular","-","[1.0,1.0]","-",true,"Rule",""],[2,2,"John","unpopular","-","[0.0,0.0]","IPL: popular",true,"IPL",""],[2,2,"Justin","popular","-","[1.0,1.0]","-",true,"Rule",""],[2,2,"Justin","unpopular","-","[0.0,0.0]","IPL: popular",true,"IPL",""]]}
P|p3-dict-nonpersistent|{"0":{"('John', 'Dog')":{},"('John', 'Justin')":{},"('John', 'Mary')":{},"('Justin', 'Cat')":{},"('Justin', 'Dog')":{},"('Justin', 'Mary')":{},"('Mary', 'Cat')":{},"Cat":{},"Dog":{},"John":{},"Justin":{},"Mary":{"popular":[1,1],"unpopular":[0,0]}},"1":{"('John', 'Dog')":{},"('John', 'Justin')":{},"('John', 'Mary')":{},"('Justin', 'Cat')":{},"('Justin', 'Dog')":{},"('Justin', 'Mary')":{},"('Mary', 'Cat')":{},"Cat":{},"Dog":{},"John":{},"Justin":{"popular":[1,1],"unpopular":[0,0]},"Mary":{"popular":[1,1],"unpopular":[0,0]}},"2":{"('John', 'Dog')":{},"('John', 'Justin')":{},"('John', 'Mary')":{},"('Justin', 'Cat')":{},"('Justin', 'Dog')":{},"('Justin', 'Mary')":{},"('Mary', 'Cat')":{},"Cat":{},"Dog":{},"John":{"popular":[1,1],"unpopular":[0,0]},"Justin":{"popular":[1,1],"unpopular":[0,0]},"Mary":{"popular":[1,1],"unpopular":[0,0]}}}
P|p4-first-again-outcome|{"raised":false}
P|p4-first-again-time|4
P|p4-second-again-outcome|{"raised":false}
P|p4-second-again-time|5
P|p4-frames|[{"columns":["component","popular"],"rows":[["Mary",[1,1]]]},{"columns":["component","popular"],"rows":[["Mary",[1,1]],["Justin",[1,1]]]},{"columns":["component","popular"],"rows":[["Mary",[1,1]],["John",[1,1]],["Justin",[1,1]]]},{"columns":["component","popular"],"rows":[]},{"columns":["component","popular"],"rows":[]}]
P|p4-dict|{"0":{"('John', 'Dog')":{},"('John', 'Justin')":{},"('John', 'Mary')":{},"('Justin', 'Cat')":{},"('Justin', 'Dog')":{},"('Justin', 'Mary')":{},"('Mary', 'Cat')":{},"Cat":{},"Dog":{},"John":{},"Justin":{},"Mary":{"popular":[1,1],"unpopular":[0,0]}},"1":{"('John', 'Dog')":{},"('John', 'Justin')":{},"('John', 'Mary')":{},"('Justin', 'Cat')":{},"('Justin', 'Dog')":{},"('Justin', 'Mary')":{},"('Mary', 'Cat')":{},"Cat":{},"Dog":{},"John":{},"Justin":{"popular":[1,1],"unpopular":[0,0]},"Mary":{"popular":[1,1],"unpopular":[0,0]}},"2":{"('John', 'Dog')":{},"('John', 'Justin')":{},"('John', 'Mary')":{},"('Justin', 'Cat')":{},"('Justin', 'Dog')":{},"('Justin', 'Mary')":{},"('Mary', 'Cat')":{},"Cat":{},"Dog":{},"John":{"popular":[1,1],"unpopular":[0,0]},"Justin":{"popular":[1,1],"unpopular":[0,0]},"Mary":{"popular":[1,1],"unpopular":[0,0]}},"3":{"('John', 'Dog')":{},"('John', 'Justin')":{},"('John', 'Mary')":{},"('Justin', 'Cat')":{},"('Justin', 'Dog')":{},"('Justin', 'Mary')":{},"('Mary', 'Cat')":{},"Cat":{},"Dog":{},"John":{},"Justin":{},"Mary":{}},"4":{"('John', 'Dog')":{},"('John', 'Justin')":{},"('John', 'Mary')":{},"('Justin', 'Cat')":{},"('Justin', 'Dog')":{},"('Justin', 'Mary')":{},"('Mary', 'Cat')":{},"Cat":{},"Dog":{},"John":{},"Justin":{},"Mary":{}}}
P|p5-again-outcome|{"raised":false}
P|p5-time|4
P|p5-dict-persistent|{"0":{"('John', 'Dog')":{},"('John', 'Justin')":{},"('John', 'Mary')":{},"('Justin', 'Cat')":{},"('Justin', 'Dog')":{},"('Justin', 'Mary')":{},"('Mary', 'Cat')":{},"Cat":{},"Dog":{},"John":{},"Justin":{},"Mary":{"popular":[1,1],"unpopular":[0,0]}},"1":{"('John', 'Dog')":{},"('John', 'Justin')":{},"('John', 'Mary')":{},"('Justin', 'Cat')":{},"('Justin', 'Dog')":{},"('Justin', 'Mary')":{},"('Mary', 'Cat')":{},"Cat":{},"Dog":{},"John":{},"Justin":{"popular":[1,1],"unpopular":[0,0]},"Mary":{"popular":[1,1],"unpopular":[0,0]}},"2":{"('John', 'Dog')":{},"('John', 'Justin')":{},"('John', 'Mary')":{},"('Justin', 'Cat')":{},"('Justin', 'Dog')":{},"('Justin', 'Mary')":{},"('Mary', 'Cat')":{},"Cat":{},"Dog":{},"John":{"popular":[1,1],"unpopular":[0,0]},"Justin":{"popular":[1,1],"unpopular":[0,0]},"Mary":{"popular":[1,1],"unpopular":[0,0]}},"3":{"('John', 'Dog')":{},"('John', 'Justin')":{},"('John', 'Mary')":{},"('Justin', 'Cat')":{},"('Justin', 'Dog')":{},"('Justin', 'Mary')":{},"('Mary', 'Cat')":{},"Cat":{},"Dog":{},"John":{"popular":[1,1],"unpopular":[0,0]},"Justin":{"popular":[1,1],"unpopular":[0,0]},"Mary":{"popular":[1,1],"unpopular":[0,0]}}}
P|p6-first-time|3
P|p6-second-outcome|{"raised":false}
P|p6-second-time|3
P|p6-second-frames|[{"columns":["component","popular"],"rows":[["a",[1,1]]]},{"columns":["component","popular"],"rows":[["a",[1,1]]]},{"columns":["component","popular"],"rows":[["a",[1,1]]]}]
P|p6-second-dict|{"0":{"('a', 'b')":{},"('b', 'c')":{},"a":{"popular":[1,1],"unpopular":[0,0]},"b":{},"c":{},"d":{},"e":{},"f":{}},"1":{"('a', 'b')":{},"('b', 'c')":{},"a":{"popular":[1,1],"unpopular":[0,0]},"b":{},"c":{},"d":{},"e":{},"f":{}},"2":{"('a', 'b')":{},"('b', 'c')":{},"a":{"popular":[1,1],"unpopular":[0,0]},"b":{},"c":{},"d":{},"e":{},"f":{}}}
P|p7-alias-after-reset|[false,false]
P|p7-last-write|[false,false]
P|p8-second-outcome|{"raised":false}
P|p8-second-time|1
P|p8-second-frames|[{"columns":["component","popular"],"rows":[]}]
```
