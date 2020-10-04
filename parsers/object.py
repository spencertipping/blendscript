"""
Objects and basic object interactions.

I think it's fine if we always start with a single point and proceed using one
of a few operations:

1. Extrude along vector, expanding frontier
2. Extrude along vector, replacing frontier
3. Close current frontier with edge/face/both and jump by vector, starting a
   new frontier
"""
