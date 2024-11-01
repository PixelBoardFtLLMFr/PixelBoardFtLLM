import file_manager as fm
import statistics
import os
import traceback
import ast
import json
from scipy import stats
import dabest
import numpy as np
import pingouin as pg
import matplotlib.pyplot as plt
import seaborn as sns
import itertools
import re

pes=["zero_shot",
     "zero_shot_cot",
     "null_shot",
     "null_shot_cot",
     "few_shot",
     "few_shot-zero_shot_cot"]
data_length=100
p_threshold=0.001

def sort_by_filename(filenames:list[str])->list[str]:
    return sorted(filenames, key=lambda x: int(fm.get_file_name_without_extension(x).split('-')[0]))

def clean_string(msg:str)->str:
    msg=msg.replace("```", "")
    msg=msg.replace("python", "")
    msg=msg.replace("Python", "")
    return msg
    

def stat_test(data1, data2):
    _, p1 = stats.shapiro(data1)
    _, p2 = stats.shapiro(data2)
    
    shapiro_threshold = 0.05
    is_normal = p1 > shapiro_threshold and p2 > shapiro_threshold
    # print(">>> Shapiro p for data1:", p1)
    # print(">>> Shapiro p for data2:", p2)
    
    if is_normal:
        _, p = stats.ttest_rel(data1, data2)
        eff_size = dabest.effsize.cohens_h(data1, data2)
        eff_desc = "small" if eff_size <= 0.2 else "medium" if eff_size <= 0.5 else "large"
    else:
        val = pg.wilcoxon(data1, data2, alternative='two-sided')
        p = val['p-val'].values[0]
        eff_size = val['RBC'].values[0]
        eff_desc = "small" if abs(eff_size) < 0.3 else "medium" if abs(eff_size) < 0.5 else "large"
        
    p_value_threshold = 0.05
    
    # if p < p_value_threshold:
    #     print(">>> Significant difference, p-value:", p)
    #     print(">>> Effect size:", eff_size)
    #     if p < 0.001:
    #         print(">>> Significant difference at 0.001")
    #     if p < 0.01:
    #         print(">>> Significant difference at 0.01")
    # else:
    #     print("No significant difference")
        
    eff_size = eff_size if p < p_value_threshold else 'no_difference'
    eff_desc = eff_desc if p < p_value_threshold else 'no_difference'
    
    return is_normal, p1, p2, p, eff_size, eff_desc

def evaluate_angles(angles_str:str, target_length:int, min_val, max_val):
    try:
        # pattern=r'\[\[.*?\]\]'
        # angles_str=re.findall(pattern, angles_str)[0]
        angles_str=clean_string(angles_str)
        angles=ast.literal_eval(angles_str)
        flattened_array = list(itertools.chain.from_iterable(angles))

        incorrect_dimensions=[a for a in angles if len(a)!=target_length]
        out_of_limits=[a for a in flattened_array if a<min_val or a>max_val]

        reason="pass"
        if len(incorrect_dimensions)>0:
            reason="incorrect dimension"
        if len(out_of_limits)>0:
            reason="out of limits"

        return len(incorrect_dimensions)<=0 and len(out_of_limits)<=0, reason
    except Exception as error:
        print(traceback.format_exc())
    return False, "error"

def evaluate_facial_expression(fe:str):
    available_fes=[
        "neutral",
        "happy",
        "sad",
        "angry",
        "surprised"
    ]

    reason="pass"
    if fe.lower().replace("\"", "") not in available_fes:
        reason=f"wrong FE: {fe.lower()}"

    return fe.lower().replace("\"", "") in available_fes, reason

def evaluate_vfx(vfx:str):
    available_vfxs=["angry",
                    "heart",
                    "sleepy",
                    "spark",
                    "sweat",
                    "cloud",
                    "none"]
    
    reason="pass"
    if vfx.lower().replace("\"", "") not in available_vfxs:
        reason=f"wrong VFX: {vfx.lower}"

    return vfx.lower().replace("\"", "") in available_vfxs, reason

def evaluate_segmented_data(arms, legs, head, y_pos, fe, vfx)->int:
    try:
        judgement, reason=evaluate_angles(angles_str=arms, target_length=2, min_val=-180, max_val=180)
        if judgement==False:
            return 0, f"arms-{reason}"
        
        judgement, reason=evaluate_angles(angles_str=legs, target_length=2, min_val=-180, max_val=180)
        if judgement==False:
            return 0, f"legs-{reason}"
        
        judgement, reason=evaluate_angles(angles_str=head, target_length=1, min_val=-90, max_val=90)
        if judgement==False:
            return 0, f"head-{reason}"
        
        judgement, reason=evaluate_angles(angles_str=y_pos, target_length=1, min_val=float('-inf'), max_val=float('inf'))
        if judgement==False:
            return 0, f"y_position-{reason}"
        
        judgement, reason=evaluate_facial_expression(fe=fe)
        if judgement==False:
            return 0, f"facial_expression-{reason}"
        
        judgement, reason=evaluate_vfx(vfx=vfx)
        if judgement==False:
            return 0, f"visual_effect-{reason}"
        
        return 1, reason
    except Exception as error:
        print(traceback.format_exc())
    return 0, "unknown error"

def evaluate_combined_data(data)->int:
    try:
        myjson=data['response']
        myjson=clean_string(myjson)
        # myjson=myjson.replace("```", "")
        # myjson=myjson.replace("python", "")
        # myjson=myjson.replace("Python", "")
        myjson=json.loads(myjson)

        judgement, reason=evaluate_angles(angles_str=str(myjson["arms"]), target_length=2, min_val=-180, max_val=180)
        if judgement==False:
            return 0, f"arms-{reason}"
        
        judgement, reason=evaluate_angles(angles_str=str(myjson["legs"]), target_length=2, min_val=-180, max_val=180)
        if judgement==False:
            return 0, f"legs-{reason}"
        
        judgement, reason=evaluate_angles(angles_str=str(myjson["head"]), target_length=1, min_val=-90, max_val=90)
        if judgement==False:
            return 0, f"head-{reason}"
        
        judgement, reason=evaluate_angles(angles_str=str(myjson["y_position"]), target_length=1, min_val=float('-inf'), max_val=float('inf'))
        if judgement==False:
            return 0, f"y_position-{reason}"
        
        judgement, reason=evaluate_facial_expression(fe=myjson["facial_expression"])
        if judgement==False:
            return 0, f"facial_expression-{reason}"
        
        judgement, reason=evaluate_vfx(vfx=myjson["visual_effect"])
        if judgement==False:
            return 0, f"visual_effect-{reason}"
        return 1, reason
    except Exception as error:
        print(traceback.format_exc())
    return 0, "unknown error"

def correct_rate_evaluation(source_dir:str, target_file:str):
    combined=sort_by_filename(filenames=fm.get_files_with_extensions(directory="./responses/combined", extensions=["json"]))
    combined=[fm.read_json(path=c) for c in combined]
    segmented=[]
    for i in range(len(combined)):
        t_segmented={"arms": fm.read_json(path=f"./responses/segmented/{(i+1)}-arms.json"),
                     "legs": fm.read_json(path=f"./responses/segmented/{(i+1)}-legs.json"),
                     "head": fm.read_json(path=f"./responses/segmented/{(i+1)}-head.json"),
                     "y_position": fm.read_json(path=f"./responses/segmented/{(i+1)}-y_position.json"),
                     "facial_expression": fm.read_json(path=f"./responses/segmented/{(i+1)}-facial_expression.json"),
                     "visual_effect": fm.read_json(path=f"./responses/segmented/{(i+1)}-visual_effect.json")}
        segmented.append(t_segmented)
    
    header=["n", "segmented", "combined"]
    rows=[]
    s_rates=[]
    c_rates=[]
    # print(len(segmented))
    for i in range(len(combined)):
        s_correct=evaluate_segmented_data(arms=segmented[i]["arms"]["response"],
                                          legs=segmented[i]["legs"]["response"],
                                          head=segmented[i]["head"]["response"],
                                          y_pos=segmented[i]["y_position"]["response"],
                                          fe=segmented[i]["facial_expression"]["response"],
                                          vfx=segmented[i]["visual_effect"]["response"])
        c_correct=evaluate_combined_data(data=combined[i])

        s_rates.append(s_correct)
        c_rates.append(c_correct)
        rows.append([i+1, s_correct, c_correct])
    
    p1, p2, p, eff_size, eff_desc = stat_test(data1=s_rates, data2=c_rates)
    rows.append(["mean", statistics.mean(s_rates), statistics.mean(c_rates)])
    rows.append(["statistical_difference", p, ""])
    rows.append(["effect_size", eff_size, eff_desc])

    fm.write_csv(path=os.path.join("evaluation", "correct_rates.csv"), data=rows, header=header)
    pass

def response_time_evaluation():
    segmented=sort_by_filename(fm.get_files_with_extensions(directory="./responses/segmented", extensions=["json"]))
    segmented=[s for s in segmented if "arms" in s]
    combined=sort_by_filename(fm.get_files_with_extensions(directory="./responses/combined", extensions=["json"]))

    header=["n", "segmented", "combined"]
    rows=[]

    s_durations=[]
    c_durations=[]
    for i in range(len(segmented)):
        s_data=fm.read_json(segmented[i])
        c_data=fm.read_json(combined[i])

        s_duration=s_data['duration']
        c_duration=c_data['duration']

        s_durations.append(s_duration)
        c_durations.append(c_duration)
        rows.append([i+1, s_duration, c_duration])
    p1, p2, p, eff_size, eff_desc = stat_test(data1=s_durations, data2=c_durations)
    rows.append(["mean", statistics.mean(s_durations), statistics.mean(c_durations)])
    rows.append(["stdev", statistics.stdev(s_durations), statistics.stdev(c_durations)])
    rows.append(["statistical_difference", p, ""])
    rows.append(["effect_size", eff_size, eff_desc])

    fm.write_csv(path=os.path.join("evaluation", "response_time.csv"), data=rows, header=header)
    draw_response_time_figures(s_durations=s_durations, c_durations=c_durations)
    pass

def draw_response_time_figures(s_durations:list, c_durations:list):
    plt.figure(figsize=(8,6))
    means = [np.mean(s_durations), np.mean(c_durations)]
    std_devs = [np.std(s_durations), np.std(c_durations)]
    sns.barplot(data=[np.array(s_durations), np.array(c_durations)], palette=["#FFBA49", "#20A39E"], ci=None)
    plt.errorbar(x=[0, 1], y=means, yerr=std_devs, fmt='none', c='black', capsize=5, capthick=2, lw=2)
    plt.xticks([0, 1], ['Segmented', 'Combined'])
    plt.ylabel("in seconds")
    # Define coordinates for significance line
    x1, x2 = 0.1, 0.9  # x-coordinates of the two bars
    y = max(means) + 0.5  # y-coordinate above the bars for the significance line
    plt.plot([x1, x2], [y, y], color='black', linestyle='--', linewidth=1)  # Horizontal line
    plt.plot([x1, x1], [means[0], y], color='black', linestyle='--', linewidth=1)  # Left vertical line
    plt.plot([x2, x2], [means[1], y], color='black', linestyle='--', linewidth=1)  # Right vertical line
    plt.text((x1 + x2) / 2, y, '*', fontsize=20, ha='center', va='bottom', color='black')  # Asterisk above the line
    # plt.title('Box Plot with Mean and Standard Deviation')
    plt.show()

def generate_segmented_correct_rate(pe:str, data_length:int):
    source_dir=os.path.join("responses", "segmented", pe)
    target_file=os.path.join("evaluation", "correct_rate", "segmented")
    if not os.path.exists(target_file):
        os.makedirs(target_file)
    target_file=os.path.join(target_file, f"s_{pe}.csv")

    segmented_data=[]
    for i in range(data_length):
        t_segmented={"arms": fm.read_json(path=os.path.join(source_dir, f"{(i+1)}-arms.json")),
                     "legs": fm.read_json(path=os.path.join(source_dir, f"{(i+1)}-legs.json")),
                     "head": fm.read_json(path=os.path.join(source_dir, f"{(i+1)}-head.json")),
                     "y_position": fm.read_json(path=os.path.join(source_dir, f"{(i+1)}-y_position.json")),
                     "facial_expression": fm.read_json(path=os.path.join(source_dir, f"{(i+1)}-facial_expression.json")),
                     "visual_effect": fm.read_json(path=os.path.join(source_dir, f"{(i+1)}-visual_effect.json"))}
        segmented_data.append(t_segmented)
    
    header=["n", "judgement", "reason"]
    rows=[]
    s_rates=[]
    for i in range(data_length):
        s_correct, s_reason=evaluate_segmented_data(arms=segmented_data[i]["arms"]["response"],
                                          legs=segmented_data[i]["legs"]["response"],
                                          head=segmented_data[i]["head"]["response"],
                                          y_pos=segmented_data[i]["y_position"]["response"],
                                          fe=segmented_data[i]["facial_expression"]["response"],
                                          vfx=segmented_data[i]["visual_effect"]["response"])
        s_rates.append(s_correct)
        rows.append([i+1, s_correct, s_reason])
    rows.append(["mean", statistics.mean(s_rates), ""])
    fm.write_csv(path=target_file, data=rows, header=header)
    pass

def generate_combined_correct_rate(pe:str, data_length:int):
    source_dir=os.path.join("responses", "combined", pe)
    target_file=os.path.join("evaluation", "correct_rate", "combined")
    if not os.path.exists(target_file):
        os.makedirs(target_file)
    target_file=os.path.join(target_file, f"c_{pe}.csv")

    combined_data=[fm.read_json(path=os.path.join(source_dir, f"{(i+1)}-combined.json")) for i in range(data_length)]    
    
    header=["n", "judgement", "reason"]
    rows=[]
    c_rates=[]
    for i in range(data_length):
        c_correct, c_reason=evaluate_combined_data(data=combined_data[i])
        c_rates.append(c_correct)
        rows.append([i+1, c_correct, c_reason])
    rows.append(["mean", statistics.mean(c_rates), ""])
    fm.write_csv(path=target_file, data=rows, header=header)
    pass

def prepare_correct_rate_data():
    for pe in pes:
        generate_segmented_correct_rate(pe=pe, data_length=data_length)
        generate_combined_correct_rate(pe=pe, data_length=data_length)
    pass

def generate_segmented_response_time(pe:str, data_length:int):
    source_dir=os.path.join("responses", "segmented", pe)
    target_file=os.path.join("evaluation", "response_time", "segmented")
    if not os.path.exists(target_file):
        os.makedirs(target_file)
    target_file=os.path.join(target_file, f"s_{pe}.csv")

    segmented_data=[fm.read_json(path=os.path.join(source_dir, f"{(i+1)}-arms.json")) for i in range(data_length)]

    header=["n", "response_time"]
    rows=[]

    s_durations=[]
    for i in range(len(segmented_data)):
        s_duration=segmented_data[i]['duration']

        s_durations.append(s_duration)
        rows.append([i+1, s_duration])
    rows.append(["mean", statistics.mean(s_durations)])
    rows.append(["stdev", statistics.stdev(s_durations)])

    fm.write_csv(path=target_file, data=rows, header=header)
    pass

def generate_combined_response_time(pe:str, data_length:int):
    source_dir=os.path.join("responses", "combined", pe)
    target_file=os.path.join("evaluation", "response_time", "combined")
    if not os.path.exists(target_file):
        os.makedirs(target_file)
    target_file=os.path.join(target_file, f"c_{pe}.csv")    

    combined_data=[fm.read_json(path=os.path.join(source_dir, f"{(i+1)}-combined.json")) for i in range(data_length)]

    header=["n", "response_time"]
    rows=[]

    c_durations=[]
    for i in range(len(combined_data)):
        c_duration=combined_data[i]['duration']

        c_durations.append(c_duration)
        rows.append([i+1, c_duration])
    rows.append(["mean", statistics.mean(c_durations)])
    rows.append(["stdev", statistics.stdev(c_durations)])

    fm.write_csv(path=target_file, data=rows, header=header)
    pass

def prepare_response_time_data():
    for pe in pes:
        generate_segmented_response_time(pe=pe, data_length=data_length)
        generate_combined_response_time(pe=pe, data_length=data_length)
    pass

def compile_correct_rate():
    data={'combined':{}, 'segmented':{}}
    for pe in pes:
        data['combined'][pe]=fm.read_csv(path=os.path.join("evaluation", "correct_rate", "combined", f"c_{pe}.csv"))    
        data['segmented'][pe]=fm.read_csv(path=os.path.join("evaluation", "correct_rate", "segmented", f"s_{pe}.csv"))
    
    my_stats={} # is_normal, p1, p2, p, eff_size, eff_desc
    for pe in pes:
        data_1=[data["combined"][pe][i][1] for i in range(data_length)]
        data_2=[data["segmented"][pe][i][1] for i in range(data_length)]
        my_stats[pe]=stat_test(data1=data_1, data2=data_2)
        print(f"correct_rate pe:{pe}, is_normal:{my_stats[pe][0]}, p:{my_stats[pe][3]} --> {my_stats[pe][3]<p_threshold}")
    
    header=["Strategy"]
    header.extend([pe.replace("_", " ").replace("-", " + ").title() for pe in pes])
    header.append("Overall")
    rows=[['Combined'], ['Segmented'], ['Overall']]
    for pe in pes:
        stat_sign=""
        if my_stats[pe][3]<p_threshold:
            stat_sign="*"
        rows[0].append(f"{data['combined'][pe][-1][1]}")
        rows[1].append(f"{data['segmented'][pe][-1][1]}{stat_sign}")
    
    # strategy-wise overall performance

    c_data=[data['combined'][pe][i][1] for i in range(data_length) for pe in pes]
    c_mean=round(statistics.mean(c_data), 2)
    rows[0].append(f"{c_mean}")
    
    s_data=[data['segmented'][pe][i][1] for i in range(data_length) for pe in pes]
    s_mean=round(statistics.mean(s_data), 2)
    is_normal, p1, p2, p, eff_size, eff_desc=stat_test(data1=s_data, data2=c_data)
    stat_sign=""
    if p<p_threshold:
        stat_sign="*"
    rows[1].append(f"{s_mean}{stat_sign}")

    # pe-wise overall performance
    pew_data={}
    for pe in pes:
        pew_data[pe]=[data['combined'][pe][i][1] for i in range(data_length)]
        pew_data[pe].extend([data['segmented'][pe][i][1] for i in range(data_length)])

    baseline_pe="zero_shot"

    for pe in pes:        
        t_mean=round(statistics.mean(pew_data[pe]), 2)
        stat_sign=""
        if pe!=baseline_pe:
            is_normal, p1, p2, p, eff_size, eff_desc=stat_test(data1=pew_data[baseline_pe], data2=pew_data[pe])
            if p<p_threshold:
                stat_sign="*"
        rows[2].append(f"{t_mean}{stat_sign}")

    target_file=os.path.join('evaluation', f"correct_rate_compiled.csv")
    fm.write_csv(path=target_file, data=rows, header=header)
    pass

def compile_response_time():    
    data={'combined':{}, 'segmented':{}}
    for pe in pes:
        data['combined'][pe]=fm.read_csv(path=os.path.join("evaluation", "response_time", "combined", f"c_{pe}.csv"))
        data['segmented'][pe]=fm.read_csv(path=os.path.join("evaluation", "response_time", "segmented", f"s_{pe}.csv"))
    
    my_stats={} # is_normal, p1, p2, p, eff_size, eff_desc
    for pe in pes:
        data_1=[data["combined"][pe][i][1] for i in range(data_length)]
        data_2=[data["segmented"][pe][i][1] for i in range(data_length)]
        my_stats[pe]=stat_test(data1=data_1, data2=data_2)
        print(f"response_time pe:{pe}, is_normal:{my_stats[pe][0]}, p:{my_stats[pe][3]} --> {my_stats[pe][3]<p_threshold}")

    header=["Strategy"]
    header.extend([pe.replace("_", " ").replace("-", " + ").title() for pe in pes])
    header.append("Overall")
    rows=[['Combined'], ['Segmented'], ['Overall']]
    for pe in pes:
        stat_sign=""
        if my_stats[pe][3]<p_threshold:
            stat_sign="*"
        rows[0].append(f"{round(data['combined'][pe][-2][1], 2)} ({round(data['combined'][pe][-1][1], 2)})")    
        rows[1].append(f"{round(data['segmented'][pe][-2][1], 2)} ({round(data['segmented'][pe][-1][1], 2)}){stat_sign}")

    # strategy-wise overall performance
    c_data=[data['combined'][pe][i][1] for i in range(data_length) for pe in pes]
    c_mean=round(statistics.mean(c_data), 2)
    c_stdev=round(statistics.stdev(c_data), 2)
    rows[0].append(f"{c_mean} ({c_stdev})")

    s_data=[data['segmented'][pe][i][1] for i in range(data_length) for pe in pes]
    s_mean=round(statistics.mean(s_data), 2)
    s_stdev=round(statistics.stdev(s_data), 2)
    is_normal, p1, p2, p, eff_size, eff_desc=stat_test(data1=s_data, data2=c_data)
    stat_sign=""
    if p<p_threshold:
        stat_sign="*"
    rows[1].append(f"{s_mean} ({s_stdev}){stat_sign}")

    # pe-wise overall performance
    pew_data={}
    for pe in pes:
        pew_data[pe]=[data['combined'][pe][i][1] for i in range(data_length)]
        pew_data[pe].extend([data['segmented'][pe][i][1] for i in range(data_length)])

    baseline_pe="zero_shot"

    for pe in pes:        
        t_mean=round(statistics.mean(pew_data[pe]), 2)
        t_stdev=round(statistics.stdev(pew_data[pe]), 2)
        stat_sign=""
        if pe!=baseline_pe:
            is_normal, p1, p2, p, eff_size, eff_desc=stat_test(data1=pew_data[baseline_pe], data2=pew_data[pe])
            if p<p_threshold:
                stat_sign="*"
        rows[2].append(f"{t_mean} ({t_stdev}){stat_sign}")
    
    target_file=os.path.join('evaluation', f"response_time_compiled.csv")
    fm.write_csv(path=target_file, data=rows, header=header)
    pass

if __name__=="__main__":
    prepare_correct_rate_data()
    prepare_response_time_data()
    compile_correct_rate()
    compile_response_time()
    pass