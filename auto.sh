controller_ssh='pcvm2-13.instageni.umkc.edu'

python3 utility/ssh.py push ${contoller_ssh} mjtsai controller.py

python3 main.py switch_config graph.pickle
python3 main.py create_controller_pickle graph.pickle di-yuan_path.csv
python3 utility/ssh.py push ${contoller_ssh} mjtsai rule.pickle
python3 main.py upload_node_script graph.pickle di-yuan_path.csv
ssh mjtsai@${controller_ssh} "nohup ryu-manager /tmp/controller.py &" &
python3 main.py run_traffic graph.pickle di-yuan_path.csv result.csv
ssh mjtsai@${ssh} "pkill -f "ryu-manager" &" & 


