
%OK

hl2ss_matlab('start_subsystem_pv', '192.168.1.7', uint16(3810), logical(false))
hl2ss_matlab('open', '192.168.1.7', uint16(3810), uint16(1920), uint16(1080), uint8(30), uint64(4096), uint8(1), uint8(1), uint8(3), uint8(255), uint32(0), uint64([10, 30]), uint8(1), uint64(300));
while (true)
    response = hl2ss_matlab('get_packet', uint16(3810), uint8(0), int64(-1));
    if (response.status == 0)
        break;
    end
    pause(1);
end
hl2ss_matlab('close', uint16(3810));
hl2ss_matlab('stop_subsystem_pv', '192.168.1.7', uint16(3810));
