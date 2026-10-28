"""Bounded bidirectional joint planning against a caller's estimated geometry.

No stored trajectories, scene states or evaluator results are consumed.
Returned polylines have sampled edges, not continuous-collision guarantees.
"""
import numpy as np


def plan(start,goal,low,high,valid,*,seed=7349,iterations=2000):
    start,goal,low,high=map(lambda v:np.asarray(v,dtype=float),(start,goal,low,high))
    if not (start.shape==goal.shape==low.shape==high.shape and np.all(low<high)):
        raise ValueError('Invalid joint planning bounds')
    rng=np.random.default_rng(seed);cache={};checks=0
    def free(q):
        nonlocal checks
        if not np.isfinite(q).all() or np.any(q<low) or np.any(q>high):return False
        key=q.tobytes()
        if key not in cache:cache[key]=bool(valid(q));checks+=1
        return cache[key]
    def edge(a,b,step=.035):
        return all(free(a+u*(b-a)) for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(b-a)/step))+1)))
    if not free(start) or not free(goal):return None,dict(reason='invalid_endpoint',checks=checks)
    trees=[([start.copy()],[-1]),([goal.copy()],[-1])];flipped=False
    def extend(tree,q):
        nodes,parents=tree;index=int(np.argmin(np.linalg.norm(np.asarray(nodes)-q,axis=1)))
        a=nodes[index];distance=np.linalg.norm(q-a)
        if distance<1e-9:return index,True
        b=a+(q-a)*min(1.,.18/distance)
        if not edge(a,b):return None,False
        nodes.append(b);parents.append(index);return len(nodes)-1,distance<=.18
    def ancestry(tree,index):
        nodes,parents=tree;result=[]
        while index>=0:result.append(nodes[index]);index=parents[index]
        return result[::-1]
    path=None
    for it in range(iterations):
        sample=(goal if not flipped else start) if rng.random()<.15 else rng.uniform(low,high)
        a,_=extend(trees[0],sample)
        if a is not None:
            target=trees[0][0][a]
            for _ in range(60):
                b,reached=extend(trees[1],target)
                if b is None:break
                if reached:
                    path=ancestry(trees[0],a)+ancestry(trees[1],b)[-2::-1]
                    if flipped:path=path[::-1]
                    break
            if path is not None:break
        trees.reverse();flipped=not flipped
    if path is None:return None,dict(reason='search_exhausted',checks=checks,iterations=iterations)
    for _ in range(80):
        if len(path)<3:break
        a,b=sorted(rng.choice(len(path),2,replace=False))
        if b-a>1 and edge(path[a],path[b]):path=path[:a+1]+path[b:]
    for a,b in zip(path[:-1],path[1:]):
        if not edge(a,b,.008):return None,dict(reason='dense_edge_rejection',checks=checks)
    return path,dict(checks=checks,vertices=len(path),iterations=it+1,
                     search_edge_step_rad=.035,final_edge_step_rad=.008)
