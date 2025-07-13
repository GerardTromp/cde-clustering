def recursive_descent(item, path, visitor, *, context=None, depth=0):
    if context is None:
        context = {}

    if isinstance(item, dict):
        for k, v in item.items():
            recursive_descent(
                v,
                f"{path}.{k}" if path else k,
                visitor,
                context=context,
                depth=depth + 1,
            )
    elif isinstance(item, list):
        for i, elem in enumerate(item):
            recursive_descent(
                elem,
                f"{path}.*" if path else "*",
                visitor,
                context=context,
                depth=depth + 1,
            )
    else:
        visitor(path, item, context)
