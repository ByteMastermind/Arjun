import arjun.core.config as mem

from arjun.core.anomaly import compare
from arjun.core.requester import requester
from arjun.core.error_handler import error_handler


def bruter(request, factors, params, mode='bruteforce', _depth=0):
    """
    Tests a chunk of parameters for anomalies.
    In bruteforce mode: uses binary search to narrow down to individual params.
    In verify mode: returns the anomaly reason string.
    """
    if mem.var['kill']:
        return [] if mode == 'bruteforce' else ''

    while True:
        response = requester(request, params)
        conclusion = error_handler(response, factors)
        if conclusion == 'retry':
            continue
        elif conclusion == 'kill':
            mem.var['kill'] = True
            return [] if mode == 'bruteforce' else ''
        break

    comparison_result = compare(response, factors, params)

    if mode == 'verify':
        return comparison_result[0]

    if not comparison_result[0]:
        return []

    if _depth == 0 and len(params) > 1:
        response2 = requester(request, params)
        if type(response2) == str:
            return []
        if not compare(response2, factors, params)[0]:
            return []

    if len(params) <= 1:
        return [params]

    items = list(params.items())
    mid = len(items) // 2
    left = dict(items[:mid])
    right = dict(items[mid:])

    found = []
    if left:
        found.extend(bruter(request, factors, left, mode=mode, _depth=_depth + 1))
    if right and not mem.var['kill']:
        found.extend(bruter(request, factors, right, mode=mode, _depth=_depth + 1))

    return found
