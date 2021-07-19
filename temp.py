# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

from prefect import Client
from simmate.shortcuts import setup  # ensures setup
from simmate.database.diffusion import Pathway as Pathway_DB

# grab the pathway ids that I am going to submit
pathway_ids = (
    Pathway_DB.objects.filter(
        vaspcalca__isnull=True,
        empiricalmeasures__dimensionality_cumlengths__gte=1,
        # empiricalmeasures__oxidation_state=-1,
        empiricalmeasures__ionic_radii_overlap_cations__gt=-0.5,
        empiricalmeasures__ionic_radii_overlap_cations__lt=0.5,
        empiricalmeasures__ionic_radii_overlap_anions__gt=-0.5,
        empiricalmeasures__ionic_radii_overlap_anions__lt=0.5,
        length__lt=3.25,
        empiricalmeasures__ewald_energy__lt=0.5,
        structure__e_above_hull=0,
        # nsites_777__lte=150,
        # structure__nsites__lte=20,
    ).order_by("nsites_777", "structure__nsites", "length")
    # BUG: distinct() doesn't work for sqlite, only postgres. also you must have
    # "structure__id" as the first flag in order_by for this to work.
    # .distinct("structure__id")
    .values_list("id", flat=True)
    # .count()
    .all()[:500]
)

# connect to Prefect Cloud
client = Client()

# submit a run for each pathway
for pathway_id in pathway_ids:
    client.create_flow_run(
        flow_id="dae896f1-2078-4389-8383-0a3dab61ef2b",
        parameters={"pathway_id": pathway_id},
    )

# --------------------------------------------------------------------------------------


# from simmate.configuration.django import setup_full  # ensures setup
# from simmate.database.diffusion import EmpiricalMeasures
# queryset = EmpiricalMeasures.objects.all()  # [:5000]
# from django_pandas.io import read_frame
# df = read_frame(queryset)  # , index_col="pathway"

# from simmate.shortcuts import setup
# from simmate.database.diffusion import VaspCalcD
# queryset = VaspCalcD.objects.all()
# from django_pandas.io import read_frame
# df = read_frame(queryset)

# from simmate.shortcuts import setup
# from simmate.database.diffusion import VaspCalcA
# pids = [14695, 15038]
# queryset = VaspCalcA.objects.filter(pathway_id__in=pids).all()


# --------------------------------------------------------------------------------------

# .filter(pathway_id__in=pids)
# pids= [3036,
# 9461,
# 3040,
# 10373,
# 3033,
# 8701,
# 9143,
# 9924,
# 1220,
# 1443,
# 1496,
# 1034,]

from simmate.shortcuts import setup
from simmate.database.diffusion import Pathway as Pathway_DB
from django_pandas.io import read_frame

# AB2 225
# AB3 194
# ABC4 123
#
# interesting 2D
# ABC 166 --dogwood
# ABCD 129 --longleaf
# AB2C2D2E2 139 --longleaf
# AB2C2 164 --dogwood
# AB2C4 139
# A2B3C7 139
#
# interesting 3D
# ABC3 221
#
queryset = (
    Pathway_DB.objects.filter(
        # structure__nelement=4,
        # structure__formula_anonymous="AB2",
        # structure__chemical_system="Ca-F",
        # structure__spacegroup=225,
        # nsites_777__lte=100,
        # structure__e_above_hull=0,
        # empiricalmeasures__dimensionality__gte=1,
        # vaspcalca__energy_barrier__gte=2.0,
        # vaspcalca__energy_barrier__lte=5,
        vaspcalcb__energy_barrier__isnull=True,
        # vaspcalcb__energy_barrier__gte=0.8,
        vaspcalcb__isnull=False,
        # vaspcalcd__isnull=True,
    ).order_by("vaspcalca__energy_barrier")
    # BUG: distinct() doesn't work for sqlite, only postgres. also you must have
    # "structure__id" as the first flag in order_by for this to work.
    .select_related("vaspcalca", "empiricalmeasures", "structure")
    # .distinct("structure__id")
    .all()
)

df = read_frame(
    queryset,
    fieldnames=[
        "id",
        "structure__formula_full",
        "structure__id",
        "structure__e_above_hull",
        "structure__spacegroup",
        "structure__formula_anonymous",
        "nsites_777",
        "nsites_101010",
        "vaspcalca__energy_barrier",
        "vaspcalcb__energy_barrier",
        "vaspcalcc__energy_barrier",
        "empiricalmeasures__dimensionality",
        "empiricalmeasures__dimensionality_cumlengths",
    ],
)


from simmate.shortcuts import setup
from simmate.database.diffusion import Pathway as Pathway_DB
from simmate.workflows.diffusion.utilities import get_oxi_supercell_path

# 51, 1686, 29326
# GOOD NEB: 77
# BAD NEB: 1046
pathway_id = 9504
path = Pathway_DB.objects.get(id=pathway_id)
get_oxi_supercell_path(path.to_pymatgen(), 10).write_path(
    f"{pathway_id}.cif",
    nimages=5,
    # idpp=True,
)

# import json
# from pymatgen.core.structure import Structure
# structure_dict = json.loads(path.vaspcalcb.structure_start_json)
# structure_start = Structure.from_dict(structure_dict)
# structure_start.to("cif", "z0.cif")
# structure_dict = json.loads(path.vaspcalcb.structure_midpoint_json)
# structure_midpoint = Structure.from_dict(structure_dict)
# structure_midpoint.to("cif", "z1.cif")
# structure_dict = json.loads(path.vaspcalcb.structure_end_json)
# structure_end = Structure.from_dict(structure_dict)
# structure_end.to("cif", "z2.cif")

# linear path from start to end
# images = structure_start.interpolate(structure_end, interpolate_lattices=True)
# test = [image.to(filename=f"{n}.cif") for n, image in enumerate(images)]


# from simmate.database.diffusion import Pathway as Pathway_DB
# path_db = Pathway_DB.objects.get(id=55).to_pymatgen().write_path("test.cif", nimages=3)

# set the executor to a locally ran executor
# from prefect.executors import DaskExecutor
# workflow.executor = DaskExecutor(address="tcp://152.2.172.72:8786")

# from simmate.shortcuts import setup  # ensures setup
# from simmate.database.diffusion import Pathway
# from simmate.workflows.diffusion.vaspcalc_b import workflow
# result = workflow.run(pathway_id=4, vasp_cmd="mpirun -n 16 vasp_std")

# module load openmpi_3.0.0/gcc_6.3.0
# mpirun -n 44 /21dayscratch/scr/j/a/jacksund/vasp_build/vasp/5.4.4/bin/vasp

# from simmate.shortcuts import setup
# from simmate.database.diffusion import VaspCalcB
# queryset = VaspCalcB.objects.get(pathway=1234)
# pathway_ids = [1643,2791,1910,2688,2075,2338,3199,2511,3231,3186,2643]
# queryset = VaspCalcB.objects.filter(pathway__in=pathway_ids).all()


from simmate.shortcuts import setup
from simmate.database.diffusion import VaspCalcB
queryset = VaspCalcB.objects.filter(energy_barrier__isnull=True).all()

# import datetime
# from simmate.shortcuts import setup
# from simmate.database.diffusion import VaspCalcA
# queryset = VaspCalcA.objects.filter(status="S", updated_at__gte=datetime.date(2021,4,26)).all()
# from django_pandas.io import read_frame
# df = read_frame(queryset)


# These are the pathways that failed for NEB and I am retrying
	id
0	3209
1	27318
2	11454
3	3198
4	10316
5	1049
6	9847
7	760
8	462
9	8701
10	1112
11	638
12	1306
13	21278
14	112
15	21276
16	2487
17	29455
18	8059
19	989
20	327
21	351
22	8906
23	15060
24	25955
25	9515
26	108
27	10739
28	27926
29	29458
----------------
30	13009
31	1757
32	3850
33	3702
34	207
35	676
36	1016
37	28365
38	1373
39	15057
40	250
41	28367
42	3132
43	18511
44	15436
45	853
46	824
47	472
48	2756
49	27919
50	11907
51	828
52	10228
53	24011
54	5845
55	7544
56	7852
57	8859
58	3409
59	3430
60	3703
61	20371
62	31775
63	1537
64	20755
65	10737
66	170
67	11749
68	3176
69	1705
70	7853
71	3197
72	8285
73	20406
74	9511
75	1191
76	13959
77	249
78	867
79	256
80	3835
81	1590
82	22317
83	964
84	33522
85	627
86	1223
87	13258
88	4140
89	3869
90	1643
91	7523
92	20231
93	323
94	20997
95	19496
96	9677
97	13963
98	103
99	20004
100	448
101	9671
102	12710
103	3346
104	1235
105	1021
106	352
107	20263
108	9455
109	8467
110	23899
111	9510
112	419
113	9843
114	3872
115	129
116	1529
117	7362
118	4143
119	1739
120	1843
121	10272
122	203
123	3849
124	15440
125	110
126	3861
127	2154
128	501
129	1155
130	17809
131	20703
132	957
133	1915
134	15446
135	10435
136	15452
137	457
138	14023
139	155
140	34952
141	22316
142	762
143	3051
144	9470
145	8989
146	2502
147	1526
148	695
149	22903
150	8521
151	1878
152	849
153	3637
154	555
155	34758
156	15455
157	114
158	912
159	1545
160	18065
161	357
162	9534
163	16
164	744
165	25952
166	13662
167	1020
168	427
169	2488
170	2509
171	3945
172	17779
173	11068
174	18007
175	36352
176	15
177	4146
178	34746
179	9835
180	8945
181	5566
182	11003
183	2843
184	68
185	2855
186	523
187	22689
188	3380
189	939
190	2318
191	241
192	18847
193	4035
194	34652
195	2851
196	378
197	17842
198	562
199	691
200	6304
201	33854
202	319
203	2988
204	19657
205	851
206	11039
207	18029
208	8948
209	2504
210	619
211	37128
212	20123
213	623
214	1784
215	8314
216	494
217	4147
218	409
219	2655
220	1002
221	18627
222	5843
223	2849
224	9296
225	18224
226	7689
227	18661
228	7919
229	22328
230	581
231	10285
232	1327
233	505
234	1363
235	12980
236	5489
237	10283
238	12983
239	1723
240	32925
241	10248
242	30387
243	974
244	8766
245	9852
246	1787
247	34633
248	1830
249	1075
250	2214
251	14678
252	5245
253	13707
254	1145
255	10433
256	423
257	842
258	10056
259	908
260	6825
261	9631
262	13096
263	1165
264	1573
265	22327
266	2896
267	2511
268	1874
269	9844
270	1193
271	8769
272	21871
273	3339
274	573
275	10579
276	1724
277	1030
278	17391
279	9753
280	629
281	124
282	8772
283	749
284	9742
285	2513
286	526
287	102
288	463
289	1562
290	100
291	10357
292	1522
293	116
294	831
295	10436
296	9752
297	25634
298	12892
299	3018
300	945
301	1572
302	1763
303	12965
304	51
305	111
306	3020
307	16374
308	52
309	1115
310	11005
311	512
312	206
313	2331
314	10834
315	757
316	1571
317	3381
318	9846
319	1483
320	33853
321	5308
322	5
323	1923
324	1974
325	1053
326	3171
327	574
328	750
329	1351
330	7119
331	10508
332	1967
333	2059
334	2496
335	2056
336	25315
337	2120
338	1489
339	2766
340	19597
341	2804
342	28518
343	3426
344	2372
345	1997
346	3421
347	2519
348	16382
349	5120
350	4350
351	859
352	1496
353	9771
354	1237
355	10069
356	3341
357	2894
358	2311
359	40851
360	2024
361	1872
362	2741
363	6757
364	491
365	4460
366	2743
367	1291
368	24750
369	3394
370	38370
371	14246
372	8462
373	7375
374	6831
375	3334
376	200
377	2269
378	2377
379	1904
380	1186
381	28495
382	1926
383	873
384	666
385	3384
386	2481
387	3029
388	17584
389	10376
390	24539
391	4073
392	7862
