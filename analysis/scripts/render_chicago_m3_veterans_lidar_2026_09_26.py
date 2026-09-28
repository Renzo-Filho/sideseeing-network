"""Render 2022 road-class points over 2025 ortho at the West Veterans gap."""
from __future__ import annotations

import json
from pathlib import Path
import struct

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from pyproj import Transformer
import shapely

from pilot_chicago_m3_classified_lidar_2026_09_26 import parse_header

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/results/Chicago/chicago_m3_lidar_point_pilot_2026_09_26'
WORK=ROOT/'analysis/work/chicago_m3_lidar_point_pilot_2026_09_26'
PREVIOUS=ROOT/'analysis/results/Chicago/chicago_m3_external_sources_2026_09_25'
IMAGE=ROOT/'analysis/work/chicago_m3_external_sources_2026_09_25/imagery/C_M3_01_raw.jpg'

def main():
    case=next(r for r in json.loads((PREVIOUS/'challenge_case_selection.json').read_text())['cases'] if r['case_id']=='C_M3_01')
    x,y,h=case['x'],case['y'],case['half_width_m']
    path=WORK/'13759300.las';meta=parse_header(path)
    dtype=np.dtype({'names':['X','Y','class'], 'formats':['<i4','<i4','u1'],
                    'offsets':[0,4,16],'itemsize':meta['point_record_length']})
    points=np.memmap(path,dtype=dtype,mode='r',offset=meta['point_offset'],shape=(meta['point_count'],))
    source=Transformer.from_crs(26916,6455,always_xy=True)
    west,south=source.transform(x-h,y-h);east,north=source.transform(x+h,y+h)
    scale,offset=meta['xyz_scales'],meta['xyz_offsets']
    classified=[]
    for start in range(0,len(points),1_000_000):
        part=points[start:start+1_000_000]
        selected=part['class']==11
        if not selected.any():continue
        xraw=part['X'][selected].astype(float)*scale[0]+offset[0]
        yraw=part['Y'][selected].astype(float)*scale[1]+offset[1]
        inside=(xraw>=west)&(xraw<=east)&(yraw>=south)&(yraw<=north)
        if inside.any():classified.append(np.column_stack([xraw[inside],yraw[inside]]))
    coords=np.concatenate(classified)
    to_map=Transformer.from_crs(6455,26916,always_xy=True)
    px,py=to_map.transform(coords[:,0],coords[:,1])
    bins=211
    counts,_,_=np.histogram2d(py,px,bins=(bins,bins),range=((y-h,y+h),(x-h,x+h)))
    # imshow origin upper expects north at the first row.
    counts=np.flipud(counts)
    fig,ax=plt.subplots(figsize=(10,10))
    ax.imshow(Image.open(IMAGE),extent=(x-h,x+h,y-h,y+h),origin='upper')
    overlay=np.ma.masked_where(counts<2,counts)
    ax.imshow(overlay,extent=(x-h,x+h,y-h,y+h),origin='upper',cmap='autumn',vmin=2,vmax=50,alpha=.55)
    block=shapely.from_wkt(case['geometry_wkt'])
    ax.plot(*block.exterior.xy,color='cyan',linewidth=2,label='Saved block candidate')
    import pandas as pd
    gap=pd.read_csv(ROOT/'analysis/results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26/named_street_gap_screen.csv')
    line=shapely.from_wkt(gap.loc[gap.trans_id.eq(154550),'uncovered_wkt'].item())
    ax.plot(*line.xy,color='magenta',linewidth=3,label='County-mask gap on W Veterans Pl')
    ax.set_xlim(x-h,x+h);ax.set_ylim(y-h,y+h);ax.set_aspect('equal')
    ax.legend(loc='lower left')
    ax.set_title('2022 LiDAR road-class returns over 2025 orthophoto')
    fig.tight_layout()
    fig.savefig(OUT/'veterans_class11_ortho_overlay.png',dpi=180)
    plt.close(fig)
    print('road class points in ortho extent:',len(px))

if __name__=='__main__':main()
