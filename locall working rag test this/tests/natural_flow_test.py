import sys
import os
import asyncio
import time

# Ensure we can import the engine
sys.path.append('c:\\tmp\\latest')
import memory_engine_parallel_lms as engine

def test_convo():
    print('--- STARTING NATURAL FLOW TEST ---')
    
    try:
        # Turn 1: Broad opening
        q1 = 'I remember we talked about some news from Australia recently. What was that cricket milestone again?'
        print(f'\nYou: {q1}')
        start = time.perf_counter()
        a1, metrics1 = engine.chat_logic(q1)
        end = time.perf_counter()
        print(f'AI: {a1}')
        print(f'[Metrics]: {metrics1} (Clock time: {end-start:.2f}s)')
        
        # Turn 2: Follow-up
        q2 = 'Right, Nathan Lyon. Switching gears, did our previous discussion mention anything about political anti-establishment movements in the US?'
        print(f'\nYou: {q2}')
        start = time.perf_counter()
        a2, metrics2 = engine.chat_logic(q2)
        end = time.perf_counter()
        print(f'AI: {a2}')
        print(f'[Metrics]: {metrics2} (Clock time: {end-start:.2f}s)')
        
        # Turn 3: Deep dive 
        q3 = 'That New Jersey primary with Andy Kim sounds intense. Was there anything about Trump and foreign payments in those same reports?'
        print(f'\nYou: {q3}')
        start = time.perf_counter()
        a3, metrics3 = engine.chat_logic(q3)
        end = time.perf_counter()
        print(f'AI: {a3}')
        print(f'[Metrics]: {metrics3} (Clock time: {end-start:.2f}s)')
        
    except Exception as e:
        print(f'\n[FATAL TEST ERROR]: {e}')
        import traceback
        traceback.print_exc()

    print('\n--- TEST COMPLETE ---')

if __name__ == '__main__':
    test_convo()
