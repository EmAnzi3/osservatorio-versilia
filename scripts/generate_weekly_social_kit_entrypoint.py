#!/usr/bin/env python3
"""Entrypoint del Social Kit settimanale con renderer specializzati."""

import generate_weekly_social_kit as weekly
import generate_life_expectancy_social as life_expectancy

_base_generate_post = weekly.renderer.generate_post


def generate_post(post, design, themes, destination):
    if post.get("metric") == "lifeExpectancy":
        return life_expectancy.generate_post(post, design, themes, destination)
    return _base_generate_post(post, design, themes, destination)


weekly.renderer.generate_post = generate_post

if __name__ == "__main__":
    raise SystemExit(weekly.main())
