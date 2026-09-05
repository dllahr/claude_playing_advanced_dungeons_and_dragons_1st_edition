#!/usr/bin/env python3
"""Diagnostic plots for a map extraction.

Kept separate from the extraction itself so that importing the library never
drags in matplotlib, and so the plots can be regenerated from a saved run.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image


def ecdf(open_fracs, path, t_solid=0.05, t_open=0.75):
    """ECDF and histogram of cell openness, with the decision thresholds drawn.

    The ECDF is what justifies the thresholds: on a line-art map the
    distribution is overwhelmingly bimodal, and the thresholds belong in the
    empty ground between the two spikes rather than at a round number.
    """
    v = np.sort(np.asarray(open_fracs, dtype=float))
    n = len(v)
    y = np.arange(1, n + 1) / n
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))

    ax[0].step(v, y, where='post', lw=2, color='#0057b8')
    ax[0].set_xlabel('fraction of cell NOT covered by rock')
    ax[0].set_ylabel('cumulative fraction of cells')
    ax[0].set_title('ECDF of cell openness  (n=%d)' % n)
    ax[0].set_xlim(-.02, 1.02)
    ax[0].grid(alpha=.3)

    ax[1].hist(v, bins=60, color='#0057b8')
    ax[1].set_yscale('log')
    ax[1].set_xlabel('fraction of cell NOT covered by rock')
    ax[1].set_ylabel('cells (log)')
    ax[1].set_title('histogram — the flat middle is the decision zone')
    ax[1].grid(alpha=.3)

    for a in ax:
        a.axvline(t_solid, color='tab:red', ls='--', lw=1.2)
        a.axvline(t_open, color='tab:green', ls='--', lw=1.2)
    ax[0].text(t_solid, .04, ' solid <= %.2f' % t_solid, color='tab:red',
               fontsize=9, rotation=90, va='bottom')
    ax[0].text(t_open, .04, ' open >= %.2f' % t_open, color='tab:green',
               fontsize=9, rotation=90, va='bottom')

    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)
    return path


def bimodality(df, path, t_solid=0.05, t_open=0.75):
    """Otsu separability against openness, coloured by rock/border contact."""
    fig, ax = plt.subplots(figsize=(7.5, 6))
    sc = ax.scatter(df['open_frac'], df['eta'], c=df['edges_touched'],
                    cmap='viridis', s=16, alpha=.75)
    plt.colorbar(sc, label='cell borders the rock touches (0-4)')
    ax.axvspan(t_solid, t_open, color='grey', alpha=.12)
    ax.set_xlabel('fraction of cell not covered by rock')
    ax.set_ylabel('Otsu separability eta  (between-class / total variance)')
    ax.set_title('Sharp boundary vs diffuse mark\ngrey band = ambiguous coverage')
    ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)
    return path


def masks(rock, ink, path):
    """Blue = structural rock, red = printed annotation, white = open."""
    h, w = rock.shape
    out = np.full((h, w, 3), 255, np.uint8)
    out[rock] = (40, 60, 170)
    out[ink] = (220, 30, 30)
    Image.fromarray(out).save(path)
    return path
