import file_manager as fm

def remove_duplicates(instructions):
    seen_instructions = set()
    unique_instructions = []    
    for i in instructions:
        if i['text'] not in seen_instructions:
            unique_instructions.append(i)
            seen_instructions.add(i['text'])    
    return unique_instructions

def main():
    instructions=fm.read_json('./instructions/cosine_similarities.json')
    instructions=remove_duplicates(instructions=instructions)
    instructions=instructions[:100]
    msg=""
    for i in instructions:
        msg=msg+f"\n{i['text']}"
    print(msg)
    pass

if __name__=="__main__":
    main()