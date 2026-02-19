import React, { useState } from 'react';
import {
  IconButton,
  Popover,
  Box,
  Typography,
  Tooltip,
} from '@mui/material';
import {
  HelpOutline as HelpIcon,
} from '@mui/icons-material';

interface HelpIconWithPopoverProps {
  title: string;
  content: string | React.ReactNode;
  iconColor?: 'primary' | 'secondary' | 'action' | 'disabled' | 'inherit' | 'error' | 'info' | 'success' | 'warning';
  iconSize?: 'small' | 'medium' | 'large';
}

export const HelpIconWithPopover: React.FC<HelpIconWithPopoverProps> = ({
  title,
  content,
  iconColor = 'action',
  iconSize = 'small',
}) => {
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);

  return (
    <>
      <Tooltip title="Mostra help">
        <IconButton
          onClick={handleClick}
          size={iconSize}
          sx={{ ml: 0.5 }}
        >
          <HelpIcon fontSize={iconSize} color={iconColor} />
        </IconButton>
      </Tooltip>
      
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'left',
        }}
      >
        <Box sx={{ p: 2, maxWidth: 400 }}>
          <Typography variant="subtitle2" gutterBottom fontWeight={600}>
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {content}
          </Typography>
        </Box>
      </Popover>
    </>
  );
};
