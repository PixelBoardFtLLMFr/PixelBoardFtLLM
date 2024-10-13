import file_manager as fm
import llm
import os

def get_file_name(pes:list[str], pt:str):
    filename=pt
    for pe in pes:
        filename=f"{filename}-{pe}"
    return f"{filename}.json"

def main():
    compared_pes=[[llm.PEType.ZERO_SHOT],
                  [llm.PEType.ZERO_SHOT_COT],
                  [llm.PEType.FEW_SHOT],
                  [llm.PEType.FEW_SHOT, llm.PEType.ZERO_SHOT_COT],
                  [llm.PEType.NULL_SHOT],
                  [llm.PEType.NULL_SHOT_COT]]
    prompt_types=[llm.PromptType.ARM,
                  llm.PromptType.LEG,
                  llm.PromptType.HEAD,
                  llm.PromptType.HEIGHT,
                  llm.PromptType.FE,
                  llm.PromptType.PARTICLE,
                  llm.PromptType.COMBINED]
    
    root_dir="./prompts"

    for pt in prompt_types:
        for pe in compared_pes:
            filepath=os.path.join(root_dir, get_file_name(pes=pe, pt=pt))
            prompt=llm.build_my_prompt(kind=pt, pes=pe)
            fm.write_text(path=filepath, content=prompt)
    pass

if __name__=="__main__":
    main()