"""

Usage:
    main.py switch_config <graph_pickle>
    main.py create_controller_pickle <graph_pickle> <path_file>
    main.py upload_node_script <graph_pickle> <path_file>
    main.py run_traffic <graph_pickle> <path_file> <output_file>

Options:
    -h --help Show this screen

"""
from docopt import docopt

from utility.geni import GENI
from utility import network as nw

def main():
    args = docopt(__doc__)
    if args['switch_config']:
        I = GENI(args['<graph_pickle>'])
        I.set_ofproto_v1_3()
        I.set_arp_table()
        I.set_flow_table()
    
    elif args['create_controller_pickle']:
        net = nw.net()
        net.set_topo(args['<graph_pickle>'])

        rule = nw.rule()
        rule.set_path( args['<path_file>'])
        rule.add_path_into_net( net )

        controller = nw.controller()
        controller.add_path_into_controller( net )
        controller.output_pickle()
    elif args['upload_node_script']:
        net = nw.net()
        net.set_topo(args['<graph_pickle>'])

        rule = nw.rule()
        rule.set_path( args['<path_file>'])
        rule.add_path_into_net( net )

        print('[WARN] clean the geni folders')
        net.clean_geni_folder()
        print('[WARN] upload node scripts')
        net.upload_node_script()
    elif args['run_traffic']:
        net = nw.net()
        net.set_topo(args['<graph_pickle>'])

        rule = nw.rule()
        rule.set_path( args['<path_file>'])
        rule.add_path_into_net( net )
        
        print('[WARN] run the sever')
        net.run_server()
        print('[WARN] run the traffic')
        net.run_traffic()
        
        net.download_node_data( args['<path_file>'], args['<output_file>'] )




if __name__ == '__main__':
    main()
